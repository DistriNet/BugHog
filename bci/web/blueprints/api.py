import json
import logging
import os

from flask import Blueprint, request

from bci.app import sock
from bci.evaluations.logic import evaluation_factory
from bci.main import Main as bci_api
from bci.web.clients import Clients

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__, url_prefix='/api')


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
    data = request.json.copy()
    params = evaluation_factory(data)
    if start_thread(bci_api.run, args=[params]):
        return {
            'status': 'OK'
        }
    else:
        return {
            'status': 'NOK'
        }


@api.route('/evaluation/stop/', methods=['POST'])
def stop_evaluation():
    data = request.json.copy()
    forcefully = data.get('forcefully', False)
    if forcefully:
        bci_api.stop_forcefully()
    else:
        bci_api.stop_gracefully()
    return {
        'status': 'OK'
    }


@api.route('/database/connect/', methods=['POST'])
def connect_database():
    if start_thread(bci_api.connect_to_database):
        return {
            'status': 'OK'
        }
    else:
        return {
            'status': 'NOK'
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
            if params := message.get('params', None):
                Clients.associate_params(ws, params)
            if message.get('info', False):
                Clients.push_info(ws)
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


@api.route('/tests/<string:project>/', methods=['GET'])
def get_tests(project: str):
    tests = bci_api.get_mech_groups_of_evaluation_framework('custom', project=project)
    return {
        'status': 'OK',
        'tests': tests
    }


@api.route('/results/', methods=['PUT'])
def get_html_plot():
    params = request.json.copy()
    plot_html, nb_of_evaluations = bci_api.get_html_plot(params)
    return {
        'status': 'OK',
        'nb_of_evaluations': nb_of_evaluations,
        'plot_html': plot_html
    }


@api.route('/log/', methods=['POST'])
def log():
    # TODO: emit logs of workers in central log
    return {
        'status': 'OK'
    }


@api.route('/data/', methods=['PUT'])
def data_source():
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
