import logging

from flask import Blueprint, current_app, render_template

from bughog.integration_tests.evaluation_configurations import get_eval_parameters_list
from bughog.integration_tests.verify_results import verify
from bughog.main import Main

logger = logging.getLogger(__name__)
test = Blueprint('test', __name__, url_prefix='/test')


def __get_main() -> Main:
    if main := current_app.config['main']:
        return main
    raise Exception('Main object is not instantiated')


@test.route('/')
def index():
    all_experiments = __get_main().evaluation_framework.get_experiments('IntegrationTests')
    elegible_experiments = [experiment[0] for experiment in all_experiments if experiment[1]]
    eval_parameters_list = get_eval_parameters_list(elegible_experiments)
    verification_results = verify(eval_parameters_list)
    return render_template('integration_tests.html', verification_results=verification_results)
