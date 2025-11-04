import logging

from flask import Blueprint, render_template

from bughog.integration_tests.verify_results import verify_all

logger = logging.getLogger(__name__)
test = Blueprint('test', __name__, url_prefix='/test')


@test.route('/')
def index():
    return render_template('integration_tests.html', verification_results=verify_all())
