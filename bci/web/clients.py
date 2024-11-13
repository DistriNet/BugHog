import json
import threading
from venv import logger

from simple_websocket import Server


class Clients:
    __semaphore = threading.Semaphore()
    __clients: dict[Server, dict | None] = {}

    @staticmethod
    def add_client(ws_client: Server):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = None

    @staticmethod
    def __remove_disconnected_clients():
        with Clients.__semaphore:
            Clients.__clients = {k: v for k, v in Clients.__clients.items() if k.connected}

    @staticmethod
    def associate_params(ws_client: Server, params: dict):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = params
        Clients.push_results(ws_client)

    @staticmethod
    def associate_project(ws_client: Server, project: str):
        # Technical debt: this method is to quickly associate a project with a client.
        # This is necessary to update the `runnable` exclamation mark in the UI when a main page is added to an experiment.
        # This functionality should be included in the `associate_params`.
        # Then, missing params should be checked server-side instead of client-side, as is the case now.
        with Clients.__semaphore:
            if not (params := Clients.__clients.get(ws_client, None)):
                params = {}
            params['project'] = project
            Clients.__clients[ws_client] = params
            Clients.push_experiments(ws_client)

    @staticmethod
    def push_results(ws_client: Server):
        from bci.main import Main as bci_api

        if params := Clients.__clients.get(ws_client, None):
            revision_data, version_data = bci_api.get_data_sources(params)
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

    @staticmethod
    def push_results_to_all():
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_results(ws_client)

    @staticmethod
    def push_info(ws_client: Server, *requested_vars: str):
        from bci.main import Main as bci_api

        update = {}
        all = not requested_vars or 'all' in requested_vars
        if 'db_info' in requested_vars or all:
            update['db_info'] = bci_api.get_database_info()
        if 'logs' in requested_vars or all:
            update['logs'] = bci_api.get_logs()
        if 'state' in requested_vars or all:
            update['state'] = bci_api.get_state()
        ws_client.send(json.dumps({'update': update}))

    @staticmethod
    def push_info_to_all(*requested_vars: str):
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_info(ws_client, *requested_vars)

    @staticmethod
    def push_experiments(ws_client: Server):
        from bci.main import Main as bci_api

        client_info = Clients.__clients[ws_client]
        if client_info is None:
            logger.error('Could not find any associated info for this client')
            return

        project = client_info.get('project', None)
        if project:
            experiments = bci_api.get_mech_groups_of_evaluation_framework('custom', project)
            ws_client.send(json.dumps({'update': {'experiments': experiments}}))

    @staticmethod
    def push_experiments_to_all():
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_experiments(ws_client)
