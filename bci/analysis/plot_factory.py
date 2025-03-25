from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import PlotParameters
from bci.version_control.state_result_factory import StateResultFactory


class PlotFactory:

    @staticmethod
    def get_plot_revision_data(params: PlotParameters) -> dict:
        revision_docs = MongoDB().get_documents_for_plotting(params)
        revision_results = PlotFactory.__add_outcome_info(params, revision_docs)
        return revision_results

    @staticmethod
    def get_plot_version_data(params: PlotParameters) -> dict:
        version_docs = MongoDB().get_documents_for_plotting(params, releases=True)
        version_results = PlotFactory.__add_outcome_info(params, version_docs)
        return version_results

    @staticmethod
    def validate_params(params: PlotParameters) -> list[str]:
        missing_parameters = []
        if not params.mech_group:
            missing_parameters.append('selected experiment')
        if not params.target_mech_id:
            missing_parameters.append('reproduction ID')
        if not params.browser_name:
            missing_parameters.append('browser')
        if not params.database_collection:
            missing_parameters.append('database collection')
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
    def __add_outcome_info(params: PlotParameters, docs: list):
        if not docs:
            return {
                'revision_number': [],
                'browser_version': [],
                'browser_version_str': [],
                'outcome': []
            }
        docs_with_outcome = []
        state_result_factory = StateResultFactory(params.mech_group)

        for doc in docs:
            state_result_data = doc['results']
            state_result = state_result_factory.get_result(state_result_data)
            new_doc = {
                'revision_number': doc['state']['revision_number'],
                'browser_version': int(doc['browser_version'].split('.')[0]),
                'browser_version_str': doc['browser_version'].split('.')[0]
            }
            if state_result.is_dirty:
                new_doc['outcome'] = 'Error'
                docs_with_outcome.append(new_doc)
            elif state_result.reproduced:
                new_doc['outcome'] = 'Reproduced'
                docs_with_outcome.append(new_doc)
            else:
                new_doc['outcome'] = 'Not reproduced'
                docs_with_outcome.append(new_doc)
        docs_with_outcome = PlotFactory.__transform_to_bokeh_compatible(docs_with_outcome)
        return docs_with_outcome
