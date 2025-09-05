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
    def associate_subject_type(ws_client: Server, subject_type: str):
        with Clients.__semaphore:
            if not (params := Clients.__clients.get(ws_client, None)):
                params = {}
            params['subject_type'] = subject_type
            Clients.__clients[ws_client] = params
            Clients.push_experiments(ws_client)
        # Clients.push_previous_cli_options(ws_client)

    @staticmethod
    def associate_subject(ws_client: Server, params: dict):
        with Clients.__semaphore:
            Clients.__clients[ws_client] = params
        # Clients.push_previous_cli_options(ws_client)

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
            # Clients.push_previous_cli_options(ws_client)

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
        project = client_info.get('project')
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

    # @staticmethod
    # def push_previous_cli_options(ws_client: Server):
    #     if params := Clients.__clients.get(ws_client, None):
    #         previous_cli_options = MongoDB().get_previous_cli_options(params)
    #         ws_client.send(json.dumps({'update': {'previous_cli_options': previous_cli_options}}))
