import json
import logging
import os
import threading

from flask import Blueprint, current_app, redirect, request

import bci.browser.support as browser_support
from bci.database.mongo.mongodb import MongoDB
import bci.evaluations.logic as application_logic
from bci.analysis.plot_factory import PlotFactory
from bci.app import sock
from bci.configuration import Global, Loggers
from bci.evaluations.logic import MissingParametersException, PlotParameters
from bci.integration_tests.evaluation_configurations import get_eval_parameters_list
from bci.main import Main
from bci.web.clients import Clients

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__, url_prefix='/api')

THREAD = None


def __start_thread(func, args=None):
    global THREAD
    if args is None:
        args = []
    if THREAD and THREAD.is_alive():
        raise AttributeError()
    else:
        THREAD = threading.Thread(target=func, args=args)
        THREAD.start()


def __get_main() -> Main:
    if main := current_app.config['main']:
        return main
    raise Exception('Main object is not instantiated')


@api.before_request
def check_readiness():
    try:
        pass
        # _ = ____get_main()
    except Exception as e:
        logger.critical(e)
        return {
            'status': 'NOK',
            'msg': 'BugHog is not ready',
            'info': {
                'log': Loggers.get_logs()
            }
        }


@api.after_request
def add_headers(response):
    if 'DEVELOPMENT' in os.environ and os.environ['DEVELOPMENT'] == '1':
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = '*'
    return response


'''
Starting and stopping processses
'''


@api.route('/evaluation/start/', methods=['POST'])
def start_evaluation():
    if request.json is None:
        return {
            'status': 'NOK',
            'msg': "No evaluation parameters found"
        }

    data = request.json.copy()
    try:
        params = application_logic.evaluation_factory(data)
        __start_thread(__get_main().run, args=[params])
        return {
            'status': 'OK'
        }
    except MissingParametersException:
        return {
            'status': 'NOK',
            'msg': 'Could not start evaluation due to missing parameters'
        }
    except AttributeError:
        return {
            'status': 'NOK',
            'msg': 'Evaluation thread is already running'
        }


@api.route('/evaluation/stop/', methods=['POST'])
def stop_evaluation():
    if request.json is None:
        return {
            'status': 'NOK',
            'msg': "No stop parameters found"
        }

    data = request.json.copy()
    forcefully = data.get('forcefully', False)
    if forcefully:
        __get_main().activate_stop_forcefully()
    else:
        __get_main().activate_stop_gracefully()
    return {
        'status': 'OK'
    }


'''
Requesting information
'''


@sock.route('/socket/', bp=api)
def init_websocket(ws):
    logger.info('Client connected')
    Clients.add_client(ws)
    while True:
        message = ws.receive()
        if message is None:
            break
        try:
            message = json.loads(message)
            if params := message.get('new_params', None):
                Clients.associate_params(ws, params)
            if params := message.get('select_project', None):
                Clients.associate_project(ws, params)
            if requested_variables := message.get('get', []):
                __get_main().push_info(ws, *requested_variables)
        except ValueError:
            logger.warning('Ignoring invalid message from client.')
    ws.send('Connected to BugHog')


@api.route('/browsers/', methods=['GET'])
def get_browsers():
    return {
        'status': 'OK',
        'browsers': [browser_support.get_chromium_support(), browser_support.get_firefox_support()]
    }


@api.route('/projects/', methods=['GET'])
def get_projects():
    return {
        'status': 'OK',
        'projects': __get_main().evaluation_framework.get_projects()
    }


@api.route('/projects/', methods=['POST'])
def create_project():
    if request.json is None:
        return {
            'status': 'NOK',
            'msg': "No parameters found"
        }
    project_name = request.json.get('project_name')
    try:
        __get_main().evaluation_framework.create_empty_project(project_name)
        return {
            'status': 'OK'
        }
    except AttributeError as e:
        return {
            'status': 'NOK',
            'msg': str(e)
        }


@api.route('/system/', methods=['GET'])
def get_system_info():
    return {
        'status': 'OK',
        'cpu_count': os.cpu_count() if os.cpu_count() else 2
    }


@api.route('/log/', methods=['POST'])
def log():
    # TODO: emit logs of workers in central log
    return {
        'status': 'OK'
    }


@api.route('/data/', methods=['PUT'])
def data_source():
    if request.json is None:
        return {
            'status': 'NOK',
            'msg': "No data parameters found"
        }

    params = request.json.copy()
    plot_params = PlotParameters.from_dict(params)
    if missing_params := PlotFactory.validate_params(plot_params):
        return {
            'status': 'NOK',
            'msg': f'Missing plot parameters: {missing_params}'
        }
    return {
            'status': 'OK',
            'revision': PlotFactory.get_plot_revision_data(params),
            'version': PlotFactory.get_plot_version_data(params)
        }

@api.route('/poc/<string:project>/', methods=['GET'])
def get_experiments(project: str):
    experiments = __get_main().evaluation_framework.get_mech_groups(project)
    return {
        'status': 'OK',
        'experiments': experiments
    }


@api.route('/poc/<string:project>/<string:poc>/', methods=['GET'])
def poc(project: str, poc: str):
    return {
        'status': 'OK',
        'tree': __get_main().evaluation_framework.get_poc_structure(project, poc)
    }


@api.route('/poc/<string:project>/<string:poc>/<string:file>/', methods=['GET', 'POST'])
def poc_file_content(project: str, poc: str, file: str):
    domain = request.args.get('domain', '')
    path = request.args.get('path', '')
    if request.method == 'GET':
        return {
            'status': 'OK',
            'content': __get_main().evaluation_framework.get_poc_file(project, poc, domain, path, file)
        }
    else:
        if not request.json:
            return {
                'status': 'NOK',
                'msg': 'No content to update file with'
            }
        data = request.json.copy()
        content = data['content']
        success = __get_main().evaluation_framework.update_poc_file(project, poc, domain, path, file, content)
        if success:
            return {
                'status': 'OK'
            }
        else :
            return {
                'status': 'NOK'
            }


@api.route('/poc/<string:project>/<string:poc>/', methods=['POST'])
def add_page(project: str, poc: str):
    if request.json is None:
        return {
            'status': 'NOK',
            'msg': "No page parameters found"
        }

    data = request.json.copy()
    domain = data['domain']
    path = data['page']
    file_type = data['file_type']
    try:
        __get_main().evaluation_framework.add_page(project, poc, domain, path, file_type)
        return {
            'status': 'OK'
        }
    except AttributeError as e:
        return {
            'status': 'NOK',
            'msg': str(e)
        }


@api.route('/poc/<string:project>/<string:poc>/config', methods=['POST'])
def add_config(project: str, poc: str):
    if request.json is None:
        return {
            'status': 'NOK',
            'msg': "No parameters found"
        }
    data = request.json.copy()
    type = data['type']
    success = __get_main().evaluation_framework.add_config(project, poc, type)
    if success:
        return {
            'status': 'OK'
        }
    else:
        return {
            'status': 'NOK'
        }


@api.route('/poc/domain/', methods=['GET'])
def get_available_domains():
    return {
        'status': 'OK',
        'domains': Global.get_available_domains()
    }


@api.route('/poc/<string:project>/', methods=['POST'])
def create_experiment(project: str):
    if request.json is None:
        return {
            'status': 'NOK',
            'msg': "No experiment parameters found"
        }

    data = request.json.copy()
    if 'poc_name' not in data.keys():
        return {
            'status': 'NOK',
            'msg': 'Missing experiment name'
        }
    poc_name = data['poc_name']
    try:
        __get_main().evaluation_framework.create_empty_poc(project, poc_name)
        return {
            'status': 'OK'
        }
    except AttributeError as e:
        return {
            'status': 'NOK',
            'msg': str(e)
        }


@api.route('/data/remove/', methods=['POST'])
def remove_datapoint():
    if (params := application_logic.TestParameters.from_dict(request.json)) is None:
        return {
            'status': 'NOK',
            'msg': "No parameters found"
        }
    __get_main().remove_datapoint(params)
    return {
        'status': 'OK'
    }


@api.route('/test/start/', methods=['POST'])
def integration_tests_start():
    # Remove all previous data
    MongoDB().remove_all_data_from_collection('integrationtests_chromium')
    MongoDB().remove_all_data_from_collection('integrationtests_firefox')
    # Start integration tests
    all_experiments = __get_main().evaluation_framework.get_mech_groups('IntegrationTests')
    elegible_experiments = [experiment[0] for experiment in all_experiments if experiment[1]]
    eval_parameters_list = get_eval_parameters_list(elegible_experiments)
    __start_thread(__get_main().run, args=[eval_parameters_list])
    return redirect('/test/')


@api.route('/test/continue/', methods=['POST'])
def integration_tests_continue():
    all_experiments = __get_main().evaluation_framework.get_mech_groups('IntegrationTests')
    elegible_experiments = [experiment[0] for experiment in all_experiments if experiment[1]]
    eval_parameters_list = get_eval_parameters_list(elegible_experiments)
    __start_thread(__get_main().run, args=[eval_parameters_list])
    return redirect('/test/')
