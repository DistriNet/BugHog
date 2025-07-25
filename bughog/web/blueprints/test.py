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
    eval_parameters_list = []
    for subject_type in factory.get_all_subject_types():
        all_experiments = factory.create_experiments(subject_type)
        experiments = all_experiments.get_experiments('IntegrationTests')
        elegible_experiments = [experiment[0] for experiment in experiments if experiment[1]]
        new_eval_parameters_list = evaluation_configurations.get_eval_parameters_list(subject_type, elegible_experiments)
        eval_parameters_list.extend(new_eval_parameters_list)
    verification_results = verify(eval_parameters_list)
    return render_template('integration_tests.html', verification_results=verification_results)
