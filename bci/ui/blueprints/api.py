import os
import threading

from flask import Blueprint, request

from bci.evaluations.logic import evaluation_factory
from bci.main import Main as bci_api

api = Blueprint('api', __name__, url_prefix='/api')
THREAD = None


def instantiate_main_object():
    bci_api.initialize()


def start_thread(func, args=[]) -> bool:
    global THREAD
    if THREAD and THREAD.is_alive():
        return False
    else:
        THREAD = threading.Thread(target=func, args=args)
        THREAD.start()
        return True


start_thread(instantiate_main_object)


@api.before_request
def check_readiness():
    if not bci_api.is_ready():
        return {
            'status': 'NOK',
            'msg': 'BugHog is not ready.'
        }


@api.after_request
def add_headers(response):
    if 'DEVELOPMENT' in os.environ:
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


@api.route('/info/', methods=['GET'])
def get_info():

    return {
        'status': 'OK',
        'info': {
            'database': bci_api.get_database_info(),
            'log': bci_api.get_logs(),
            'running': bci_api.is_running()
        }
    }


@api.route('/browsers/', methods=['GET'])
def get_browsers():
    return {
        'status': 'OK',
        'browsers': bci_api.get_browsers()
    }


@api.route('/projects/', methods=['GET'])
def get_projects():
    return {
        'status': 'OK',
        'projects': bci_api.get_projects_of_custom_framework()
    }


@api.route('/options/<string:browser_name>/', methods=['GET'])
def get_options(browser_name: str):
    try:
        options = bci_api.get_browser_options(browser_name)
        return {
            'status': 'OK',
            'options': options
        }
    except Exception as e:
        return {
            'status': 'NOK',
            'msg': str(e)
        }


@api.route('/extensions/<string:browser_name>/', methods=['GET'])
def get_extensions(browser_name: str):
    try:
        extensions = bci_api.get_available_extensions(browser_name)
        return {
            'status': 'OK',
            'extensions': extensions
        }
    except Exception as e:
        return {
            'status': 'NOK',
            'msg': str(e)
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
