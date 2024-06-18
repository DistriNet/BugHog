import json
import threading

from simple_websocket import Server


class Clients:
    __semaphore = threading.Semaphore()
    __clients: dict[Server] = {}

    @staticmethod
    def add_client(ws_client: Server):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = None

    @staticmethod
    def __remove_disconnected_clients():
        with Clients.__semaphore:
            Clients.__clients = {
                k: v for k, v in Clients.__clients.items() if k.connected
            }

    @staticmethod
    def associate_params(ws_client: Server, params: dict):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = params
        Clients.push_results(ws_client)

    @staticmethod
    def push_results(ws_client: Server):
        from bci.main import Main as bci_api

        if params := Clients.__clients.get(ws_client, None):
            revision_data, version_data = bci_api.get_data_sources(params)
            ws_client.send(
                json.dumps(
                    {
                        "update": {
                            "plot_data": {
                                "revision_data": revision_data,
                                "version_data": version_data,
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
    def push_info(ws_client: Server, *requested_vars: list[str]):
        from bci.main import Main as bci_api

        update = {}
        all = not requested_vars or "all" in requested_vars
        if "db_info" in requested_vars or all:
            update["db_info"] = bci_api.get_database_info()
        if "logs" in requested_vars or all:
            update["logs"] = bci_api.get_logs()
        if "state" in requested_vars or all:
            update["state"] = bci_api.get_state()
        ws_client.send(json.dumps({"update": update}))

    @staticmethod
    def push_info_to_all(*requested_vars: list[str]):
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_info(ws_client, *requested_vars)
