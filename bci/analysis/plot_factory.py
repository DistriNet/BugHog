from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import PlotParameters


class PlotFactory:

    @staticmethod
    def get_plot_revision_data(params: PlotParameters, db: MongoDB) -> dict:
        revision_docs = db.get_documents_for_plotting(params)
        revision_results = PlotFactory.__add_outcome_info(params, revision_docs)
        return revision_results

    @staticmethod
    def get_plot_version_data(params: PlotParameters, db: MongoDB) -> dict:
        version_docs = db.get_documents_for_plotting(params, releases=True)
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
    def __add_outcome_info(params: PlotParameters, docs: dict):
        if not docs:
            return {
                'revision_number': [],
                'browser_version': [],
                'browser_version_str': [],
                'outcome': []
            }

        docs_with_outcome = []
        target_mech_id = params.target_mech_id if params.target_mech_id else params.mech_group

        for doc in docs:
            # DISCLAIMER:
            # Because Nginx takes care of all HTTPS traffic, flask (which doubles as proxy) only sees HTTP traffic.
            # Browser <--HTTPS--> Nginx <--HTTP--> Flask

            # Backwards compatibility
            requests_to_target = list(filter(lambda x: f'/report/?leak={target_mech_id}' in x['url'], doc['results']['requests']))
            # New way
            if [req_var for req_var in doc['results']['req_vars'] if req_var['var'] == 'reproduced' and req_var['val'] == 'OK'] or \
                    [log_var for log_var in doc['results']['log_vars'] if log_var['var'] == 'reproduced' and log_var['val'] == 'OK']:
                reproduced = True
            else:
                reproduced = False

            new_doc = {
                'revision_number': doc['state']['revision_number'],
                'browser_version': int(doc['browser_version'].split('.')[0]),
                'browser_version_str': doc['browser_version'].split('.')[0]
            }
            if doc['dirty']:
                new_doc['outcome'] = 'Error'
                docs_with_outcome.append(new_doc)
            elif len(requests_to_target) > 0 or reproduced:
                new_doc['outcome'] = 'Reproduced'
                docs_with_outcome.append(new_doc)
            else:
                new_doc['outcome'] = 'Not reproduced'
                docs_with_outcome.append(new_doc)
        docs_with_outcome = PlotFactory.__transform_to_bokeh_compatible(docs_with_outcome)
        return docs_with_outcome
