import logging

from flask import Blueprint, current_app, render_template

from bughog.integration_tests import evaluation_configurations
from bughog.integration_tests.verify_results import verify
from bughog.main import Main
from bughog.subject import factory

logger = logging.getLogger(__name__)
test = Blueprint('test', __name__, url_prefix='/test')


def __get_main() -> Main:
    if main := current_app.config['main']:
        return main
    raise Exception('Main object is not instantiated')


@test.route('/')
def index():
    all_experiments = factory.create_experiments('web_browser')
    experiments = all_experiments.get_experiments('IntegrationTests')
    elegible_experiments = [experiment[0] for experiment in experiments if experiment[1]]
    eval_parameters_list = evaluation_configurations.get_eval_parameters_list(elegible_experiments)
    verification_results = verify(eval_parameters_list)
    return render_template('integration_tests.html', verification_results=verification_results)
