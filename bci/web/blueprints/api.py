import json
import logging
import os
import threading

from flask import Blueprint, request

from bci.app import sock
from bci.evaluations.logic import evaluation_factory
from bci.main import Main as bci_api
from bci.web.clients import Clients

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__, url_prefix='/api')

THREAD = None


def __start_thread(func, args=None) -> bool:
    global THREAD
    if args is None:
        args = []
    if THREAD and THREAD.is_alive():
        return False
    else:
        THREAD = threading.Thread(target=func, args=args)
        THREAD.start()
        return True


@api.before_request
def check_readiness():
    if not bci_api.is_ready():
        return {
            'status': 'NOK',
            'msg': 'BugHog is not ready',
            'info': {
                'log': bci_api.get_logs(),
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
    params = evaluation_factory(data)
    if __start_thread(bci_api.run, args=[params]):
        return {
            'status': 'OK'
        }
    else:
        return {
            'status': 'NOK'
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
        bci_api.stop_forcefully()
    else:
        bci_api.stop_gracefully()
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
                Clients.push_info(ws, *requested_variables)
        except ValueError:
            logger.warning('Ignoring invalid message from client.')
    ws.send('Connected to BugHog')


@api.route('/browsers/', methods=['GET'])
def get_browsers():
    return {
        'status': 'OK',
        'browsers': bci_api.get_browser_support()
    }


@api.route('/projects/', methods=['GET'])
def get_projects():
    return {
        'status': 'OK',
        'projects': bci_api.get_projects_of_custom_framework()
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
    revision_data, version_data = bci_api.get_data_sources(params)
    if revision_data or version_data:
        return {
            'status': 'OK',
            'revision': revision_data,
            'version': version_data
        }
    else:
        return {
            'status': 'NOK',
            'msg': 'Invalid type'
        }


@api.route('/poc/<string:project>/', methods=['GET'])
def get_experiments(project: str):
    experiments = bci_api.get_mech_groups_of_evaluation_framework('custom', project)
    return {
        'status': 'OK',
        'experiments': experiments
    }


@api.route('/poc/<string:project>/<string:poc>/', methods=['GET'])
def poc(project: str, poc: str):
    return {
        'status': 'OK',
        'tree': bci_api.get_poc(project, poc)
    }


@api.route('/poc/<string:project>/<string:poc>/<string:file>/', methods=['GET', 'POST'])
def get_poc_file_content(project: str, poc: str, file: str):
    domain = request.args.get('domain', '')
    path = request.args.get('path', '')
    if request.method == 'GET':
        return {
            'status': 'OK',
            'content': bci_api.get_poc_file(project, poc, domain, path, file)
        }
    else:
        if not request.json:
            return {
                'status': 'NOK',
                'msg': 'No content to update file with'
            }
        data = request.json.copy()
        success = bci_api.update_poc_file(project, poc, domain, path, file, data['content'])
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
    success = bci_api.add_page(project, poc, data['domain'], data['page'], data['file_type'])
    if success:
        return {
            'status': 'OK'
        }
    else:
        return {
            'status': 'NOK'
        }


@api.route('/poc/<string:project>/<string:poc>/config', methods=['POST'])
def add_config(project: str, poc: str):
    data = request.json.copy()
    success = bci_api.add_config(project, poc, data['type'])
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
        'domains': bci_api.get_available_domains()
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
    if bci_api.create_empty_poc(project, data['poc_name']):
        return {
            'status': 'OK'
        }
    else:
        return {
            'status': 'NOK',
            'msg': 'Could not create experiment'
        }
