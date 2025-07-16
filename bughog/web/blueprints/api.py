import json
import logging
import os
import threading

from flask import Blueprint, current_app, request

import bughog.parameters as application_logic
from bughog.app import sock
from bughog.configuration import Global, Loggers
from bughog.main import Main
from bughog.parameters import MissingParametersException
from bughog.subject import factory
from bughog.subject.factory import get_subject_availability
from bughog.version_control.state.base import State
from bughog.web.clients import Clients

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
        return {'status': 'NOK', 'msg': 'BugHog is not ready', 'info': {'log': Loggers.get_logs()}}


@api.after_request
def add_headers(response):
    if 'DEVELOPMENT' in os.environ and os.environ['DEVELOPMENT'] == '1':
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = '*'
    return response


"""
Starting and stopping processses
"""


@api.route('/evaluation/start/', methods=['POST'])
def start_evaluation():
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No evaluation parameters found'}

    data = request.json.copy()
    try:
        database_params = Global.get_database_params()
        params = application_logic.evaluation_factory(data, database_params)
        __start_thread(__get_main().run, args=[params])
        return {'status': 'OK'}
    except MissingParametersException:
        return {'status': 'NOK', 'msg': 'Could not start evaluation due to missing parameters'}
    except AttributeError:
        return {'status': 'NOK', 'msg': 'Evaluation thread is already running'}


@api.route('/evaluation/stop/', methods=['POST'])
def stop_evaluation():
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No stop parameters found'}

    data = request.json.copy()
    forcefully = data.get('forcefully', False)
    if forcefully:
        __get_main().activate_stop_forcefully()
    else:
        __get_main().activate_stop_gracefully()
    return {'status': 'OK'}


"""
Requesting information
"""


@sock.route('/socket/', bp=api)
def init_websocket(ws):
    logger.info('Client connected')
    Clients.add_client(ws)
    ws.send(json.dumps({'status': 'OK', 'msg': 'Connected to BugHog backend.'}))
    while True:
        message = ws.receive()
        if message is None:
            break
        try:
            message = json.loads(message)
            if params := message.get('select_subject_type', None):
                Clients.associate_subject_type(ws, params)
            if params := message.get('new_subject', None):
                Clients.associate_subject(ws, params)
            if params := message.get('new_params', None):
                Clients.associate_params(ws, params)
            if params := message.get('select_project', None):
                Clients.associate_project(ws, params)
            if requested_variables := message.get('get', []):
                __get_main().push_info(ws, *requested_variables)
        except ValueError:
            logger.warning('Ignoring invalid message from client.')


@api.route('/subject/', methods=['GET'])
def get_subjects():
    return {'status': 'OK', 'subject_availability': get_subject_availability()}


@api.route('/system/', methods=['GET'])
def get_system_info():
    return {'status': 'OK', 'cpu_count': os.cpu_count() if os.cpu_count() else 2}


@api.route('/log/', methods=['POST'])
def log():
    # TODO: emit logs of workers in central log
    return {'status': 'OK'}


@api.route('/poc/<string:subject_type>/', methods=['GET'])
def get_projects(subject_type: str):
    return {'status': 'OK', 'projects': factory.create_experiments(subject_type).get_projects()}


@api.route('/poc/<string:subject_type>/', methods=['POST'])
def create_project(subject_type: str):
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No parameters found'}
    project_name = request.json.get('project_name')
    try:
        factory.create_experiments(subject_type).create_empty_project(project_name)
        return {'status': 'OK'}
    except AttributeError as e:
        return {'status': 'NOK', 'msg': str(e)}


@api.route('/poc/<string:subject_type>/<string:project>/', methods=['GET'])
def get_experiments(subject_type: str, project: str):
    experiments = factory.create_experiments(subject_type).get_experiments(project)
    return {'status': 'OK', 'experiments': experiments}


@api.route('/poc/<string:subject_type>/<string:project>/<string:poc>/', methods=['GET'])
def poc(subject_type: str, project: str, poc: str):
    return {'status': 'OK', 'tree': factory.create_experiments(subject_type).get_poc_structure(project, poc)}


@api.route('/poc/<string:subject_type>/<string:project>/<string:poc>/<string:file>/', methods=['GET', 'POST'])
def poc_file_content(subject_type: str, project: str, poc: str, file: str):
    domain = request.args.get('domain', '')
    path = request.args.get('path', '')
    if request.method == 'GET':
        return {
            'status': 'OK',
            'content': factory.create_experiments(subject_type).get_poc_file(project, poc, domain, path, file),
        }
    else:
        if not request.json:
            return {'status': 'NOK', 'msg': 'No content to update file with'}
        data = request.json.copy()
        content = data['content']
        success = factory.create_experiments(subject_type).update_poc_file(project, poc, domain, path, file, content)
        if success:
            return {'status': 'OK'}
        else:
            return {'status': 'NOK'}


@api.route('/poc/<string:subject_type>/<string:project>/<string:poc>/', methods=['POST'])
def add_page(subject_type: str, project: str, poc: str):
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No page parameters found'}

    data = request.json.copy()
    domain = data['domain']
    path = data['page']
    file_type = data['file_type']
    try:
        factory.create_experiments(subject_type).add_page(project, poc, domain, path, file_type)
        return {'status': 'OK'}
    except AttributeError as e:
        return {'status': 'NOK', 'msg': str(e)}


@api.route('/poc/<string:subject_type>/<string:project>/<string:poc>/config', methods=['POST'])
def add_config(subject_type: str, project: str, poc: str):
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No parameters found'}
    data = request.json.copy()
    type = data['type']
    success = factory.create_experiments(subject_type).add_config(project, poc, type)
    if success:
        Clients.push_experiments_to_all()
        return {'status': 'OK'}
    else:
        return {'status': 'NOK'}


@api.route('/poc/domain/', methods=['GET'])
def get_available_domains():
    return {'status': 'OK', 'domains': Global.get_available_domains()}


@api.route('/poc/<string:subject_type>/<string:project>/', methods=['POST'])
def create_experiment(subject_type: str, project: str):
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No experiment parameters found'}

    data = request.json.copy()
    if 'poc_name' not in data.keys():
        return {'status': 'NOK', 'msg': 'Missing experiment name'}
    poc_name = data['poc_name']
    try:
        factory.create_experiments(subject_type).create_empty_poc(project, poc_name)
        Clients.push_experiments_to_all()
        return {'status': 'OK'}
    except AttributeError as e:
        return {'status': 'NOK', 'msg': str(e)}


@api.route('/data/remove/', methods=['POST'])
def remove_datapoint():
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No evaluation parameters found'}

    data = request.json.copy()
    database_params = Global.get_database_params()
    params_list = application_logic.evaluation_factory(data, database_params)
    if len(params_list) < 1:
        return {'status': 'NOK', 'msg': 'Could not construct removal parameters'}
    subject_type = params_list[0].subject_configuration.subject_type
    subject_name = params_list[0].subject_configuration.subject_name
    state = State.from_dict(subject_type, subject_name, data)
    __get_main().remove_datapoint(params_list[0], state)
    return {'status': 'OK'}


# @api.route('/test/start/', methods=['POST'])
# def integration_tests_start():
#     # Remove all previous data
#     MongoDB().remove_all_data_from_collection('integrationtests_chromium')
#     MongoDB().remove_all_data_from_collection('integrationtests_firefox')
#     # Start integration tests
#     all_experiments = __get_main().evaluation_framework.get_experiments('IntegrationTests')
#     elegible_experiments = [experiment[0] for experiment in all_experiments if experiment[1]]
#     eval_parameters_list = get_eval_parameters_list(elegible_experiments)
#     __start_thread(__get_main().run, args=[eval_parameters_list])
#     return redirect('/test/')


# @api.route('/test/continue/', methods=['POST'])
# def integration_tests_continue():
#     all_experiments = __get_main().evaluation_framework.get_experiments('IntegrationTests')
#     elegible_experiments = [experiment[0] for experiment in all_experiments if experiment[1]]
#     eval_parameters_list = get_eval_parameters_list(elegible_experiments)
#     __start_thread(__get_main().run, args=[eval_parameters_list])
#     return redirect('/test/')
