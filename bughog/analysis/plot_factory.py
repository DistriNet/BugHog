from bughog.database.mongo.mongodb import MongoDB
from bughog.evaluation.experiment_result import ExperimentResult
from bughog.parameters import EvaluationParameters


class PlotFactory:
    @staticmethod
    def get_plot_commit_data(params: EvaluationParameters) -> dict:
        commit_docs = MongoDB().get_documents_for_plotting(params)
        return PlotFactory.__add_outcome_info(commit_docs)

    @staticmethod
    def get_plot_release_data(params: EvaluationParameters) -> dict:
        release_docs = MongoDB().get_documents_for_plotting(params, releases=True)
        return PlotFactory.__add_outcome_info(release_docs)

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
    def __add_outcome_info(docs: list):
        if not docs:
            return {'commit_nb': [], 'subject_version': [], 'subject_version_str': [], 'outcome': []}
        docs_with_outcome = []

        for doc in docs:
            result_variables = set((variables[0], variables[1]) for variables in doc['result']['variables'])
            new_doc = {
                'commit_nb': doc['state']['commit_nb'],
                'commit_url': doc['state']['commit_url'] if 'commit_url' in doc['state'] else None,
                'subject_version': int(doc['subject_version'].split('.')[0]),
                'subject_version_str': doc['subject_version'].split('.')[0],
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
