import logging
import os
import sys

from bughog.configuration import Loggers
from bughog.database.mongo.mongodb import MongoDB
from bughog.evaluation.evaluation import Evaluation
from bughog.parameters import EvaluationParameters
from bughog.version_control.state.base import State

# This logger argument is set explicitly so when this file is ran as a script, it will still use the logger configuration
logger = logging.getLogger('bci.worker')


def __run_by_worker() -> None:
    """
    Executes evaluation based on given parameters.
    Should only be called by worker.
    """
    Loggers.configure_loggers()
    if len(sys.argv) < 3:
        logger.info('Worker did not receive enough arguments.')
        os._exit(0)

    params = EvaluationParameters.deserialize(sys.argv[1])
    state = State.deserialize(sys.argv[2])
    MongoDB().connect(params.database_params)

    logger.info('Worker started')
    run(params, state)
    logger.info('Worker finished, exiting...')

    logging.shutdown()
    os._exit(0)


def run(params: EvaluationParameters, state: State):
    """
    Executes evaluation based on given parameters.
    """
    evaluation = Evaluation(params.subject_configuration.subject_type)
    try:
        evaluation.evaluate(params, state, is_worker=True)
    except Exception:
        logger.fatal('An exception occurred during evaluation', exc_info=True)
        logging.shutdown()
        os._exit(1)


if __name__ == '__main__':
    __run_by_worker()
