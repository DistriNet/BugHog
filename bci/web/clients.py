import json
import threading

from simple_websocket import Server

from bci.main import Main as bci_api


class Clients:

    __semaphore = threading.Semaphore()
    __clients: dict[Server] = {}

    @staticmethod
    def add_client(ws_client: Server):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = ws_client

    @staticmethod
    def associate_params(ws_client: Server, params: dict):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = params
        Clients.push_results(ws_client)

    @staticmethod
    def push_results(ws_client: Server):
        if params := Clients.__clients.get(ws_client, None):
            revision_data, version_data = bci_api.get_data_sources(params)
            ws_client.send(json.dumps({
                'results': {
                    'revision_data': revision_data,
                    'version_data': version_data,
                }
            }))

    @staticmethod
    def push_info(ws_client: Server):
        ws_client.send(json.dumps({
            'info': {
                'database': bci_api.get_database_info(),
                'log': bci_api.get_logs(),
                'running': bci_api.is_running()
            }
        }))

    @staticmethod
    def broadcast_change(content: list=None):
        for client_ws in Clients.__clients.keys():
            if not content:
                Clients.push_info(client_ws)
                Clients.push_results(client_ws)
            if 'results' in content:
                Clients.push_results(client_ws)
            if 'info' in content:
                Clients.push_info(client_ws)
