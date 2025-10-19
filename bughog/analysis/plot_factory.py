from bughog.database.mongo.mongodb import MongoDB
from bughog.evaluation.experiment_result import ExperimentResult
from bughog.parameters import EvaluationParameters
from bughog.subject import factory
from bughog.subject.state_oracle import StateOracle


class PlotFactory:
    @staticmethod
    def get_plot_commit_data(params: EvaluationParameters) -> dict:
        commit_docs = MongoDB().get_documents_for_plotting(params)
        state_oracle = factory.get_subject_from_params(params).state_oracle
        return PlotFactory.__add_outcome_info(commit_docs, state_oracle)

    @staticmethod
    def get_plot_release_data(params: EvaluationParameters) -> dict:
        release_docs = MongoDB().get_documents_for_plotting(params, releases=True)
        return PlotFactory.__add_outcome_info(release_docs, None)

    @staticmethod
    def validate_params(params: EvaluationParameters) -> list[str]:
        missing_parameters = []
        if not params.evaluation_range.experiment_name:
            missing_parameters.append('selected experiment')
        if not params.subject_configuration.subject_type:
            missing_parameters.append('subject_type')
        if not params.subject_configuration.subject_name:
            missing_parameters.append('subject_name')
        return missing_parameters

    @staticmethod
    def __transform_to_bokeh_compatible(docs: list) -> dict:
        new_docs = {}
        for d in docs:
            for key, value in d.items():
                if key not in new_docs:
                    new_docs[key] = []
                new_docs[key].append(value)
        return new_docs

    @staticmethod
    def __add_outcome_info(docs: list, state_oracle: StateOracle|None):
        if not docs:
            return {'commit_nb': [], 'major_version': [], 'version_printed_by_executable': [], 'outcome': []}

        docs_with_outcome = []
        for doc in docs:
            result_variables = set((variables[0], variables[1]) for variables in doc['result']['variables'])

            commit_nb = doc['state']['commit_nb']
            commit_id = doc['state']['commit_id']
            if state_oracle:
                commit_url = state_oracle.get_commit_url(commit_nb, commit_id)
            else:
                commit_url = None

            new_doc = {
                'commit_nb': commit_nb,
                'commit_url': commit_url,
                'major_version': doc['state'].get('major_version', None), # commit states don't have this field
                'version_printed_by_executable': doc['subject_version'],
            }
            if doc['dirty']:
                new_doc['outcome'] = 'Error'
                docs_with_outcome.append(new_doc)
            elif ExperimentResult.poc_is_reproduced(result_variables):
                new_doc['outcome'] = 'Reproduced'
                docs_with_outcome.append(new_doc)
            else:
                new_doc['outcome'] = 'Not reproduced'
                docs_with_outcome.append(new_doc)
        docs_with_outcome = PlotFactory.__transform_to_bokeh_compatible(docs_with_outcome)
        return docs_with_outcome
