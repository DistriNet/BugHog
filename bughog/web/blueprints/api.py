import json
import logging
import os

from flask import Blueprint, current_app, redirect, request

import bughog.parameters as application_logic
from bughog import config
from bughog.app import sock
from bughog.database.mongo.mongodb import MongoDB
from bughog.integration_tests import evaluation_configurations, verify_results
from bughog.main import Main
from bughog.parameters import MissingParametersError
from bughog.subject import factory
from bughog.subject.factory import get_all_subject_availability
from bughog.web.clients import Clients
from bughog.web.evaluation_thread import run_eval_thread, run_experiment_thread

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__, url_prefix='/api')


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
        return {'status': 'NOK', 'msg': 'BugHog is not ready', 'info': {'log': config.Loggers.get_logs()}}


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
        database_params = config.get_database_params()
        params = application_logic.create_evaluation_params(data, database_params)
        run_eval_thread(__get_main(), params)
        return {'status': 'OK'}
    except MissingParametersError:
        return {'status': 'NOK', 'msg': 'Could not start evaluation due to missing parameters.'}


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


@api.route('/experiment/start/', methods=['POST'])
def start_experiment():
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No experiment parameters found'}

    data = request.json.copy()
    try:
        database_params = config.get_database_params()
        params = application_logic.create_experiment_params(data, database_params)
        __get_main().remove_datapoint(params)
        run_experiment_thread(__get_main(), params)
        return {'status': 'OK'}
    except MissingParametersError:
        return {'status': 'NOK', 'msg': 'Could not start experiment due to missing parameters.'}


@api.route('/experiment/remove/', methods=['POST'])
def remove_experiment_result():
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No experiment parameters found'}

    data = request.json.copy()
    try:
        database_params = config.get_database_params()
        params = application_logic.create_experiment_params(data, database_params)
        __get_main().remove_datapoint(params)
        return {'status': 'OK'}
    except MissingParametersError:
        return {'status': 'NOK', 'msg': 'Could not remove experiment result due to missing parameters.'}


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
            if params := message.get('new_params', None):
                Clients.associate_params(ws, params)
            if requested_variables := message.get('get', []):
                __get_main().push_info(ws, *requested_variables)
            if params_dict := message.get('request_experiment_result', None):
                params = application_logic.create_experiment_params(params_dict, config.get_database_params())
                Clients.push_complete_experiment_result(params)
        except ValueError:
            logger.warning('Ignoring invalid message from client.')


@api.route('/subject/', methods=['GET'])
def get_subjects():
    return {'status': 'OK', 'subject_availability': get_all_subject_availability()}


@api.route('/subject/<string:subject_name>/versions/', methods=['GET'])
def get_subject_versions(subject_name: str):
    from bughog.version_control.conversion import bughog_service
    versions = bughog_service.find_all_versions(subject_name)
    return {'status': 'OK', 'versions': versions}


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
    experiments = factory.create_experiments(subject_type)
    dir_tree = experiments.get_experiment_dir_tree(project, poc)
    return {'status': 'OK', 'tree': dir_tree}


@api.route('/poc/<string:subject_type>/<string:project>/<string:poc>/<string:file_name>/', methods=['GET', 'POST'])
@api.route(
    '/poc/<string:subject_type>/<string:project>/<string:poc>/<string:file_name>/<string:folder_name>/',
    methods=['GET', 'POST'],
)
def poc_file_content(subject_type: str, project: str, poc: str, file_name: str, folder_name: str | None = None):
    if request.method == 'GET':
        return {
            'status': 'OK',
            'content': factory.create_experiments(subject_type).get_poc_file(project, poc, folder_name, file_name),
        }
    else:
        if not request.json:
            return {'status': 'NOK', 'msg': 'No content to update file with'}
        data = request.json.copy()
        content = data['content']
        success = factory.create_experiments(subject_type).update_poc_file(
            project, poc, folder_name, file_name, content
        )
        if success:
            return {'status': 'OK'}
        else:
            return {'status': 'NOK'}


@api.route('/poc/<string:subject_type>/<string:project>/<string:poc>/', methods=['POST', 'DELETE'])
def add_folder_or_file(subject_type: str, project: str, poc: str):
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No page parameters found'}
    data = request.json.copy()
    folder_name = data['folder_name']
    file_name = data['file_name']

    if request.method == 'POST':
        try:
            factory.create_experiments(subject_type).add_folder_or_file(project, poc, folder_name, file_name)
            Clients.push_experiments_to_all()
            return {'status': 'OK'}
        except AttributeError as e:
            return {'status': 'NOK', 'msg': str(e)}
    else:
        try:
            factory.create_experiments(subject_type).remove_folder_or_file(project, poc, folder_name, file_name)
            Clients.push_experiments_to_all()
            return {'status': 'OK'}
        except AttributeError as e:
            return {'status': 'NOK', 'msg': str(e)}


@api.route('/poc/domain/', methods=['GET'])
def get_available_domains():
    return {'status': 'OK', 'domains': config.get_available_domains()}


@api.route('/poc/<string:subject_type>/<string:project>/', methods=['POST'])
def create_experiment(subject_type: str, project: str):
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No experiment parameters found'}

    data = request.json.copy()
    if 'poc_name' not in data.keys():
        return {'status': 'NOK', 'msg': 'Missing experiment name'}
    poc_name = data['poc_name']
    try:
        factory.create_experiments(subject_type).add_experiment(project, poc_name)
        Clients.push_experiments_to_all()
        return {'status': 'OK'}
    except AttributeError as e:
        return {'status': 'NOK', 'msg': str(e)}


@api.route('/data/remove/', methods=['POST'])
def remove_datapoint():
    if request.json is None:
        return {'status': 'NOK', 'msg': 'No evaluation parameters found'}

    data = request.json.copy()
    if not isinstance(data, dict):
        return {'status': 'NOK', 'msg': 'Received dataformat is not a dictionary.'}
    if (data.get('type')) not in ['release', 'commit']:
        return {'status': 'NOK', 'msg': 'Type argument should be release or commit.'}
    database_params = config.get_database_params()
    try:
        params = application_logic.create_experiment_params(data, database_params)
        __get_main().remove_datapoint(params)
    except MissingParametersError:
        return {'status': 'NOK', 'msg': 'Could not remove datapoint due to missing parameters'}
    return {'status': 'OK'}


@api.route('/test/continue/', methods=['POST'])
def integration_tests_continue():
    clean_slate = request.args.get('clean_slate', 'no')
    eval_parameters_list = []
    for subject_type in verify_results.get_all_testable_subject_types():
        all_experiments = factory.create_experiments(subject_type)
        experiments = all_experiments.get_experiments(verify_results.TEST_PROJECT_NAME)
        elegible_experiments = [experiment[0] for experiment in experiments if experiment[1]]
        new_eval_parameters_list = evaluation_configurations.get_eval_parameters_list(
            subject_type, elegible_experiments
        )
        if clean_slate == 'yes':
            MongoDB().remove_all_data_for(new_eval_parameters_list)
        eval_parameters_list.extend(new_eval_parameters_list)
    run_eval_thread(__get_main(), eval_parameters_list)
    return redirect('/test/')


@api.route('/cache/executables/delete', methods=['POST'])
def remove_cached_executables():
    subject_type = request.form.get('subject_type')
    subject_name = request.form.get('subject_name')
    state_name = request.form.get('state_name')

    if not subject_type or not subject_name or not state_name:
        return {'status': 'NOK', 'msg': 'Missing parameters.'}

    __get_main().remove_cached_executable(subject_type, subject_name, state_name)
    return {'status': 'OK'}
