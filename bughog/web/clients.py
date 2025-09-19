import json
import logging
import threading

from simple_websocket import Server

from bughog.analysis.plot_factory import PlotFactory
from bughog.configuration import Global
from bughog.parameters import MissingParametersException, evaluation_factory
from bughog.subject import factory

logger = logging.getLogger(__name__)


class Clients:
    __semaphore = threading.Semaphore()
    __clients: dict[Server, dict] = {}

    @staticmethod
    def add_client(ws_client: Server):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = {}

    @staticmethod
    def __remove_disconnected_clients():
        with Clients.__semaphore:
            Clients.__clients = {k: v for k, v in Clients.__clients.items() if k.connected}

    @staticmethod
    def associate_params(ws_client: Server, new_params: dict):
        with Clients.__semaphore:
            old_params = Clients.__clients.get(ws_client, {})
            updated_keys = Clients.get_keys_with_different_values(old_params, new_params)
            Clients.__clients[ws_client] = new_params
            if 'subject_type' in updated_keys:
                Clients.push_experiments(ws_client)
            if 'project_name' in updated_keys:
                Clients.push_experiments(ws_client)
        required_params_for_results = [
            'subject_type',
            'subject_name',
            'lower_version',
            'upper_version',
            'project_name',
            'experiment_to_plot'
        ]
        if all([new_params.get(param) is not None for param in required_params_for_results]):
            Clients.push_results(ws_client)

    @staticmethod
    def get_keys_with_different_values(dict1: dict, dict2: dict) -> list[str]:
        """
        Returns a list of keys for which dict1 and that have different values.
        """
        keys = set(dict1.keys()).union(set(dict2.keys()))
        return [key for key in keys if dict1.get(key) != dict2.get(key)]

    @staticmethod
    def push_results(ws_client: Server):
        if params := Clients.__clients.get(ws_client, None):
            if params.get('experiment_to_plot') is None:
                return
            params['experiments'] = [params['experiment_to_plot']]
            try:
                eval_params = evaluation_factory(params, Global.get_database_params())
                if len(eval_params) < 1:
                    return
                plot_params = eval_params[0].to_plot_parameters(params['experiment_to_plot'])

                if PlotFactory.validate_params(plot_params):
                    revision_data = None
                    version_data = None
                else:
                    revision_data = PlotFactory.get_plot_commit_data(plot_params)
                    version_data = PlotFactory.get_plot_release_data(plot_params)

                ws_client.send(
                    json.dumps(
                        {
                            'update': {
                                'plot_data': {
                                    'revision_data': revision_data,
                                    'version_data': version_data,
                                }
                            }
                        }
                    )
                )
            except MissingParametersException:
                logger.error('Could not update plot due to missing parameters.')

    @staticmethod
    def push_results_to_all():
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_results(ws_client)

    @staticmethod
    def push_info(ws_client: Server, update: dict):
        ws_client.send(json.dumps({'update': update}))

    @staticmethod
    def push_info_to_all(update: dict):
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_info(ws_client, update)

    @staticmethod
    def push_experiments(ws_client: Server):
        client_info = Clients.__clients[ws_client]
        if client_info is None:
            logger.error('Could not find any associated info for this client')
            return

        subject_type = client_info.get('subject_type')
        project = client_info.get('project_name')
        if project and subject_type:
            factory.invalidate_experiment_cache()
            experiments = factory.create_experiments(subject_type)
            experiments = experiments.get_experiments(project)
            ws_client.send(json.dumps({'update': {'experiments': experiments}}))

    @staticmethod
    def push_experiments_to_all():
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_experiments(ws_client)
