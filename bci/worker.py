import logging
import os
import sys

from bci.configuration import Loggers
from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.custom.custom_evaluation import CustomEvaluationFramework
from bci.evaluations.logic import WorkerParameters

# This logger argument is set explicitly so when this file is ran as a script, it will still use the logger configuration
logger = logging.getLogger('bci.worker')


def run(params: WorkerParameters):

    # Only perform configuration steps for separate workers
    if __name__ == '__main__':
        MongoDB.connect(params.database_connection_params)

    # click passes options with multiple=True as a tuple, so we convert it to a list
    # browser_cli_options = list(browser_cli_options)
    evaluation_framework = get_evaluation_framework(params)
    # browser_build, repo_state = get_browser_build_and_repo_state(params)

    evaluation_framework.evaluate(params)


def get_evaluation_framework(params: WorkerParameters):
    # TODO: we always select custom now, but still have to clean this up
    return CustomEvaluationFramework()
    # if params.evaluation_configuration.evaluation_framework == 'samesite':
    #     return SameSiteEvaluationFramework()
    # elif params.evaluation_configuration.evaluation_framework == 'custom':
    #     return CustomEvaluationFramework()
    # elif params.evaluation_configuration.evaluation_framework == 'xsleaks':
    #     return XSLeaksEvaluation()
    # else:
    #     raise AttributeError(f'Unknown framework name \'{params.evaluation_configuration.evaluation_framework}\'')


if __name__ == '__main__':
    Loggers.configure_loggers()
    if len(sys.argv) < 2:
        logger.info('Worker did not receive any arguments.')
        os._exit(0)
    args = sys.argv[1]
    params = WorkerParameters.deserialize(args)
    logger.info('Worker started')
    run(params)
    logger.info('Worker finished, exiting...')
    os._exit(0)
