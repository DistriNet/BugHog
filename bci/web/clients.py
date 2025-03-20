import json
import threading
from venv import logger

from flask import current_app
from simple_websocket import Server

from bci.analysis.plot_factory import PlotFactory
from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.logic import PlotParameters


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
    def associate_browser(ws_client: Server, params: dict):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = params
        Clients.push_previous_cli_options(ws_client)

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
            Clients.push_previous_cli_options(ws_client)

    @staticmethod
    def push_results(ws_client: Server):
        if params := Clients.__clients.get(ws_client, None):
            plot_params = PlotParameters.from_dict(params)

            if PlotFactory.validate_params(plot_params):
                revision_data = None
                version_data = None
            else:
                revision_data = PlotFactory.get_plot_revision_data(plot_params)
                version_data = PlotFactory.get_plot_version_data(plot_params)

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

        project = client_info.get('project', None)
        if project:
            from bci.main import Main
            main: Main = current_app.config['main']
            experiments = main.evaluation_framework.get_mech_groups(project)
            ws_client.send(json.dumps({'update': {'experiments': experiments}}))

    @staticmethod
    def push_experiments_to_all():
        Clients.__remove_disconnected_clients()
        for ws_client in Clients.__clients.keys():
            Clients.push_experiments(ws_client)

    @staticmethod
    def push_previous_cli_options(ws_client: Server):
        if params := Clients.__clients.get(ws_client, None):
            previous_cli_options = MongoDB().get_previous_cli_options(params)
            ws_client.send(
                json.dumps(
                    {
                        'update': {
                            'previous_cli_options': previous_cli_options
                        }
                    }
                )
            )
