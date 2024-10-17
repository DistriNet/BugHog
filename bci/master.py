import logging

import bci.database.mongo.container as mongodb_container
from bci.configuration import Global
from bci.database.mongo.mongodb import MongoDB, ServerException
from bci.distribution.worker_manager import WorkerManager
from bci.evaluations.custom.custom_evaluation import CustomEvaluationFramework
from bci.evaluations.evaluation_framework import EvaluationFramework
from bci.evaluations.logic import (
    DatabaseParameters,
    EvaluationParameters,
)
from bci.evaluations.outcome_checker import OutcomeChecker
from bci.evaluations.samesite.samesite_evaluation import SameSiteEvaluationFramework
from bci.evaluations.xsleaks.evaluation import XSLeaksEvaluation
from bci.search_strategy.bgb_search import BiggestGapBisectionSearch
from bci.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bci.search_strategy.composite_search import CompositeSearch
from bci.search_strategy.sequence_strategy import SequenceFinished, SequenceStrategy
from bci.version_control.factory import StateFactory
from bci.web.clients import Clients

logger = logging.getLogger(__name__)


class Master:
    def __init__(self):
        self.state = {'is_running': False, 'reason': 'init', 'status': 'idle'}

        self.stop_gracefully = False
        self.stop_forcefully = False

        # self.evaluations = []
        self.evaluation_framework = None
        self.worker_manager = None
        self.available_evaluation_frameworks = {}

        self.firefox_build = None
        self.chromium_build = None

        Global.initialize_folders()
        self.db_connection_params = Global.get_database_params()
        self.connect_to_database(self.db_connection_params)
        self.inititialize_available_evaluation_frameworks()
        logger.info('BugHog is ready!')

    def connect_to_database(self, db_connection_params: DatabaseParameters):
        try:
            MongoDB.connect(db_connection_params)
        except ServerException:
            logger.error('Could not connect to database.', exc_info=True)

    def run(self, eval_params: EvaluationParameters):
        self.state = {'is_running': True, 'reason': 'user', 'status': 'running'}
        self.stop_gracefully = False
        self.stop_forcefully = False

        Clients.push_info_to_all('is_running', 'state')

        browser_config = eval_params.browser_configuration
        evaluation_config = eval_params.evaluation_configuration
        evaluation_range = eval_params.evaluation_range
        sequence_config = eval_params.sequence_configuration

        logger.info(
            f'Running experiments for {browser_config.browser_name} ({", ".join(evaluation_range.mech_groups)})'
        )
        self.evaluation_framework = self.get_specific_evaluation_framework(evaluation_config.project)
        self.worker_manager = WorkerManager(sequence_config.nb_of_containers)

        try:
            search_strategy = self.create_sequence_strategy(eval_params)

            try:
                while (self.stop_gracefully or self.stop_forcefully) is False:
                    # Update search strategy with new potentially new results
                    current_state = search_strategy.next()

                    # Prepare worker parameters
                    worker_params = eval_params.create_worker_params_for(current_state, self.db_connection_params)

                    # Start worker to perform evaluation
                    self.worker_manager.start_test(worker_params)

            except SequenceFinished:
                logger.debug('Last experiment has started')
                self.state['reason'] = 'finished'

        except Exception as e:
            logger.critical('A critical error occurred', exc_info=True)
            raise e
        finally:
            # Gracefully exit
            if self.stop_gracefully:
                logger.info('Gracefully stopping experiment queue due to user end signal...')
                self.state['reason'] = 'user'
            if self.stop_forcefully:
                logger.info('Forcefully stopping experiment queue due to user end signal...')
                self.state['reason'] = 'user'
                self.worker_manager.forcefully_stop_all_running_containers()
            else:
                logger.info('Gracefully stopping experiment queue since last experiment started.')
            # MongoDB.disconnect()
            logger.info('Waiting for remaining experiments to stop...')
            self.worker_manager.wait_until_all_evaluations_are_done()
            logger.info('BugHog has finished the evaluation!')
            self.state['is_running'] = False
            self.state['status'] = 'idle'
            Clients.push_info_to_all('is_running', 'state')

    def inititialize_available_evaluation_frameworks(self):
        self.available_evaluation_frameworks['samesite'] = SameSiteEvaluationFramework()
        self.available_evaluation_frameworks['custom'] = CustomEvaluationFramework()
        self.available_evaluation_frameworks['xsleaks'] = XSLeaksEvaluation()

    @staticmethod
    def create_sequence_strategy(eval_params: EvaluationParameters) -> SequenceStrategy:
        sequence_config = eval_params.sequence_configuration
        search_strategy = sequence_config.search_strategy
        sequence_limit = sequence_config.sequence_limit
        outcome_checker = OutcomeChecker(sequence_config)
        state_factory = StateFactory(eval_params, outcome_checker)

        if search_strategy == 'bgb_sequence':
            strategy = BiggestGapBisectionSequence(state_factory, sequence_limit)
        elif search_strategy == 'bgb_search':
            strategy = BiggestGapBisectionSearch(state_factory)
        elif search_strategy == 'comp_search':
            strategy = CompositeSearch(state_factory, sequence_limit)
        else:
            raise AttributeError("Unknown search strategy option '%s'" % search_strategy)
        return strategy

    def get_specific_evaluation_framework(self, evaluation_name: str) -> EvaluationFramework:
        # TODO: we always use 'custom', in which evaluation_name is a project
        evaluation_name = 'custom'
        if evaluation_name not in self.available_evaluation_frameworks.keys():
            raise AttributeError("Could not find a framework for '%s'" % evaluation_name)
        return self.available_evaluation_frameworks[evaluation_name]

    def activate_stop_gracefully(self):
        if self.evaluation_framework:
            self.stop_gracefully = True
            self.state = {'is_running': True, 'reason': 'user', 'status': 'waiting_to_stop'}
            Clients.push_info_to_all('state')
            self.evaluation_framework.stop_gracefully()
            logger.info('Received user signal to gracefully stop.')
        else:
            logger.info('Received user signal to gracefully stop, but no evaluation is running.')

    def activate_stop_forcefully(self):
        if self.evaluation_framework:
            self.stop_forcefully = True
            self.state = {'is_running': True, 'reason': 'user', 'status': 'waiting_to_stop'}
            Clients.push_info_to_all('state')
            self.evaluation_framework.stop_gracefully()
            if self.worker_manager:
                self.worker_manager.forcefully_stop_all_running_containers()
            logger.info('Received user signal to forcefully stop.')
        else:
            logger.info('Received user signal to forcefully stop, but no evaluation is running.')

    def stop_bughog(self):
        logger.info('Stopping all running BugHog containers...')
        self.activate_stop_forcefully()
        mongodb_container.stop()
        logger.info('Stopping BugHog core...')
        exit(0)
