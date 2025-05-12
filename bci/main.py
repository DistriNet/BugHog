import logging
import time

import bci.database.mongo.container as mongodb_container
from bci.configuration import Global, Loggers
from bci.database.mongo.mongodb import MongoDB, ServerException
from bci.database.mongo.revision_cache import RevisionCache
from bci.distribution.worker_manager import WorkerManager
from bci.evaluations import experiments
from bci.evaluations.custom.custom_evaluation import CustomEvaluationFramework
from bci.evaluations.logic import (
    DatabaseParameters,
    EvaluationParameters,
    TestParameters,
)
from bci.search_strategy.bgb_search import BiggestGapBisectionSearch
from bci.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bci.search_strategy.composite_search import CompositeSearch
from bci.search_strategy.sequence_strategy import SequenceFinished, SequenceStrategy
from bci.version_control.state_factory import StateFactory
from bci.version_control.state_result_factory import StateResultFactory
from bci.web.clients import Clients

logger = logging.getLogger(__name__)


class Main:
    def __init__(self) -> None:
        self.state = {'is_running': False, 'reason': 'init', 'status': 'idle'}

        self.stop_gracefully = False
        self.stop_forcefully = False

        self.firefox_build = None
        self.chromium_build = None

        self.eval_queue = []

        Global.initialize_folders()
        self.db_connection_params = Global.get_database_params()
        self.connect_to_database(self.db_connection_params)
        RevisionCache.update()
        experiments.verify()
        self.evaluation_framework = CustomEvaluationFramework()
        logger.info('BugHog is ready!')

    def connect_to_database(self, db_connection_params: DatabaseParameters) -> None:
        try:
            MongoDB().connect(db_connection_params)
        except ServerException:
            logger.error('Could not connect to database.', exc_info=True)

    def run(self, eval_params_list: list[EvaluationParameters]) -> None:
        # Sequence_configuration settings are the same over evaluation parameters (quick fix)
        worker_manager = WorkerManager(eval_params_list[0].sequence_configuration.nb_of_containers)
        self.stop_gracefully = False
        self.stop_forcefully = False
        try:
            self.__init_eval_queue(eval_params_list)
            for eval_params in eval_params_list:
                if self.stop_gracefully or self.stop_forcefully:
                    break
                self.__update_eval_queue(eval_params.evaluation_range.mech_group, 'active')
                self.__update_state(is_running=True, reason='user', status='running', queue=self.eval_queue)
                self.run_single_evaluation(eval_params, worker_manager)

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
                worker_manager.forcefully_stop_all_running_containers()
            else:
                logger.info('Gracefully stopping experiment queue since last experiment started.')
            # MongoDB.disconnect()
            logger.info('Waiting for remaining experiments to stop...')
            worker_manager.wait_until_all_evaluations_are_done()
            logger.info('BugHog has finished the evaluation!')
            self.__update_state(is_running=False, status='idle', queue=self.eval_queue)

    def run_single_evaluation(self, eval_params: EvaluationParameters, worker_manager: WorkerManager) -> None:
        # Quick fix: we attempt a couple of retries for each evaluation, to make sure pinpointing is comprehensive.
        # TODO: Pinpoint the issue that causes pinpointing to be incomprehensive. Presumably, this is caused by not all
        # states being evaluated upon deciding for the next state to be evaluated.
        nb_of_iterations = 3
        for i in range(1, nb_of_iterations + 1):
            start_time = time.time()
            browser_name = eval_params.browser_configuration.browser_name
            experiment_name = eval_params.evaluation_range.mech_group
            search_strategy = self.create_sequence_strategy(eval_params)

            logger.info(f"Starting evaluation for experiment '{experiment_name}' with browser '{browser_name}', iteration {i}/{nb_of_iterations}.")
            try:
                while (self.stop_gracefully or self.stop_forcefully) is False:
                    # Update search strategy with new potentially new results
                    current_state = search_strategy.next()

                    # Prepare worker parameters
                    worker_params = eval_params.create_worker_params_for(current_state, self.db_connection_params)

                    # Start worker to perform evaluation
                    worker_manager.start_test(worker_params)

            except SequenceFinished:
                iteration_time = round(time.time() - start_time)
                worker_manager.wait_until_all_evaluations_are_done()
                logger.debug(f"Last experiment has finished for iteration {i}/{nb_of_iterations}. This iteration took {iteration_time}s.")

        # Retry all tests with a dirty result once.
        self.retry_dirty_tests(eval_params, worker_manager)

        self.state['reason'] = 'finished'
        self.__update_eval_queue(eval_params.evaluation_range.mech_group, 'done')

    def retry_dirty_tests(self, eval_params: EvaluationParameters, worker_manager: WorkerManager) -> None:
        state_result_factory = StateResultFactory()
        dirty_states = MongoDB().get_evaluated_states(eval_params, None, state_result_factory, dirty=True)
        if (nb_of_dirty_states := len(dirty_states)) == 0:
            logger.info("No tests are associated with a dirty result.")
            return

        logger.info(f"Retrying {nb_of_dirty_states} tests with a dirty result...")
        for dirty_state in dirty_states:
            if self.stop_gracefully or self.stop_forcefully:
                return
            worker_params = eval_params.create_worker_params_for(dirty_state, self.db_connection_params)
            test_params = worker_params.create_test_params()
            MongoDB().remove_datapoint(test_params)
            worker_manager.start_test(worker_params)
        worker_manager.wait_until_all_evaluations_are_done()
        dirty_states_after_retry = MongoDB().get_evaluated_states(eval_params, None, state_result_factory, dirty=True)
        logger.info(f"Dirty test results reduced from {nb_of_dirty_states} to {len(dirty_states_after_retry)}.")

    @staticmethod
    def create_sequence_strategy(eval_params: EvaluationParameters) -> SequenceStrategy:
        sequence_config = eval_params.sequence_configuration
        search_strategy = sequence_config.search_strategy
        sequence_limit = sequence_config.sequence_limit
        state_factory = StateFactory(eval_params)

        if search_strategy == 'bgb_sequence':
            strategy = BiggestGapBisectionSequence(state_factory, sequence_limit)
        elif search_strategy == 'bgb_search':
            strategy = BiggestGapBisectionSearch(state_factory)
        elif search_strategy == 'comp_search':
            strategy = CompositeSearch(state_factory, sequence_limit)
        else:
            raise AttributeError("Unknown search strategy option '%s'" % search_strategy)
        return strategy

    def activate_stop_gracefully(self):
        if self.evaluation_framework:
            self.stop_gracefully = True
            self.__update_state(is_running=True, reason='user', status='waiting_to_stop')
            self.evaluation_framework.stop_gracefully()
            logger.info('Received user signal to gracefully stop.')
        else:
            logger.info('Received user signal to gracefully stop, but no evaluation is running.')

    def activate_stop_forcefully(self) -> None:
        if self.evaluation_framework:
            self.stop_forcefully = True
            self.__update_state(is_running=True, reason='user', status='waiting_to_stop')
            self.evaluation_framework.stop_gracefully()
            WorkerManager.forcefully_stop_all_running_containers()
            logger.info('Received user signal to forcefully stop.')
        else:
            logger.info('Received user signal to forcefully stop, but no evaluation is running.')

    def quit_bughog(self) -> None:
        """
        Quits the bughog application, stopping all associated containers.
        """
        logger.info('Stopping all running BugHog containers...')
        self.activate_stop_forcefully()
        mongodb_container.stop()
        logger.info('Stopping BugHog core...')
        logging.shutdown()
        exit(0)

    def sigint_handler(self, sig_number, stack_frame) -> None:
        logger.debug(f'Sigint received with number {sig_number} for stack frame {stack_frame}')
        self.quit_bughog()

    def push_info(self, ws, *args) -> None:
        update = {}
        all = 'all' in args
        for arg in args:
            if arg == 'db_info' or all:
                update['db_info'] = MongoDB().get_info()
            if arg == 'logs' or all:
                update['logs'] = Loggers.get_logs()
            if arg == 'state' or all:
                update['state'] = self.state
        Clients.push_info(ws, update)

    def remove_datapoint(self, params: TestParameters) -> None:
        MongoDB().remove_datapoint(params)
        Clients.push_results_to_all()

    def __update_state(self, **kwargs) -> None:
        for key, value in kwargs.items():
            self.state[key] = value
        Clients.push_info_to_all({'state': self.state})

    def __init_eval_queue(self, eval_params_list: list[EvaluationParameters]) -> None:
        self.eval_queue = []
        for eval_params in eval_params_list:
            self.eval_queue.append({
                'experiment': eval_params.evaluation_range.mech_group,
                'state': 'pending'
            })

    def __update_eval_queue(self, experiment: str, state: str) -> None:
        for eval in self.eval_queue:
            if eval['experiment'] == experiment:
                eval['state'] = state
                return
