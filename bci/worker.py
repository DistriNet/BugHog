import logging
import os
import sys

from bci.configuration import Loggers
from bci.database.mongo.mongodb import MongoDB
from bci.evaluations.custom.custom_evaluation import CustomEvaluationFramework
from bci.evaluations.logic import WorkerParameters

# This logger argument is set explicitly so when this file is ran as a script, it will still use the logger configuration
logger = logging.getLogger('bci.worker')


def __run_by_worker() -> None:
    """
    Executes evaluation based on given parameters.
    Should only be called by worker.
    """
    Loggers.configure_loggers()
    if len(sys.argv) < 2:
        logger.info('Worker did not receive any arguments.')
        os._exit(0)
    args = sys.argv[1]

    logger.info('Worker started')
    database_connection_params = WorkerParameters.get_database_params(args)
    MongoDB().connect(database_connection_params)

    params = WorkerParameters.deserialize(args)
    run(params)
    logger.info('Worker finished, exiting...')

    logging.shutdown()
    os._exit(0)


def run(params: WorkerParameters):
    """
    Executes evaluation based on given parameters.
    """
    evaluation_framework = CustomEvaluationFramework()
    try:
        evaluation_framework.evaluate(params, is_worker=True)
    except Exception:
        logger.fatal("An exception occurred during evaluation", exc_info=True)
        logging.shutdown()
        os._exit(1)


if __name__ == '__main__':
    __run_by_worker()
