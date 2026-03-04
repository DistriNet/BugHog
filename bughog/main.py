import logging
import time

import bughog.database.mongo.container as mongodb_container
from bughog import config
from bughog.database.mongo.executable_cache import ExecutableCache
from bughog.database.mongo.mongodb import MongoDB, ServerException
from bughog.distribution.worker_manager import WorkerManager
from bughog.exceptions import SystemError, UserError
from bughog.parameters import (
    DatabaseParameters,
    EvaluationParameters,
    ExperimentParameters,
)
from bughog.search_strategy.bgb_search import BiggestGapBisectionSearch
from bughog.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bughog.search_strategy.composite_search import CompositeSearch
from bughog.search_strategy.sequence_strategy import SequenceFinished, SequenceStrategy
from bughog.subject import factory
from bughog.version_control.state_factory import StateFactory
from bughog.web.clients import Clients

logger = logging.getLogger(__name__)


class Main:
    def __init__(self) -> None:
        self.state = {'is_running': False, 'reason': 'init', 'status': 'idle'}

        self.stop_gracefully = False
        self.stop_forcefully = False

        self.eval_queue = []

        self.db_connection_params = config.get_database_params()
        self.connect_to_database(self.db_connection_params)
        factory.initialize_all_subject_folders()

        logger.info('BugHog is ready!')
        if config.settings.github_token is None:
            logger.warning(
                'BUGHOG_GITHUB_TOKEN was not configured in ./config/.env. This might result in failed API requests.'
            )

    def connect_to_database(self, db_connection_params: DatabaseParameters) -> None:
        try:
            MongoDB().connect(db_connection_params)
        except ServerException:
            logger.error('Could not connect to database.', exc_info=True)

    def run(self, eval_params_list: list[EvaluationParameters]) -> None:
        # Sequence_configuration settings are the same over evaluation parameters (quick fix)
        self.__update_state(is_running=True, reason='user', status='running')

        subject_type = eval_params_list[0].subject_configuration.subject_type
        subject_name = eval_params_list[0].subject_configuration.subject_name
        nb_of_containers = eval_params_list[0].sequence_configuration.nb_of_containers
        worker_manager = WorkerManager(subject_type, subject_name, nb_of_containers)
        self.stop_gracefully = False
        self.stop_forcefully = False
        try:
            self.__init_eval_queue(eval_params_list)
            for eval_params in eval_params_list:
                if self.stop_gracefully or self.stop_forcefully:
                    break
                self.__update_eval_queue(eval_params.experiment_name, 'active')
                self.__update_state(
                    is_running=True,
                    reason='user',
                    status='running',
                    queue=self.eval_queue,
                )
                try:
                    self.run_single_evaluation(eval_params, worker_manager)
                except (UserError, SystemError) as e:
                    # If we are running integration tests, we want to just continue with other subjects.
                    unique_subjects = set(
                        [eval_params.subject_configuration.subject_name for eval_params in eval_params_list]
                    )
                    if len(unique_subjects) == 1:
                        raise e
                except Exception:
                    logger.error(
                        f'Could not finish evaluation for {eval_params.subject_configuration.subject_name}.',
                        exc_info=True,
                    )

            # Exit handling
            if self.stop_gracefully:
                logger.info('Gracefully stopping experiment queue due to user end signal...')
                self.state['reason'] = 'user'
            elif self.stop_forcefully:
                logger.info('Forcefully stopping experiment queue due to user end signal...')
                self.state['reason'] = 'user'
                worker_manager.forcefully_stop_all_running_containers()
            else:
                logger.info('Gracefully stopping experiment queue since last experiment started.')

        except (UserError, SystemError) as e:
            logger.error(f'Evaluation stopped because of a user or system error: {e}')
            raise e
        except Exception as e:
            logger.critical('A critical error occurred', exc_info=True)
            raise e
        finally:
            logger.info('Waiting for remaining experiments to stop...')
            worker_manager.wait_until_all_evaluations_are_done()
            logger.info('BugHog has finished the evaluation!')
            self.__update_state(is_running=False, status='idle', queue=self.eval_queue)

    def run_single_evaluation(self, eval_params: EvaluationParameters, worker_manager: WorkerManager) -> None:
        # We attempt a couple of tries per evaluation, because flaky binaries might render an evaluation incomprehensive
        # when some tests return an error.
        nb_of_iterations = 3
        for i in range(1, nb_of_iterations + 1):
            start_time = time.time()
            subject = factory.get_subject_from_params(eval_params.subject_configuration)
            experiment_name = eval_params.experiment_name
            search_strategy = self.create_sequence_strategy(eval_params)

            logger.info(
                f"Starting evaluation for experiment '{experiment_name}' with '{subject.name}', iteration {i}/{nb_of_iterations}."
            )
            try:
                while (self.stop_gracefully or self.stop_forcefully) is False:
                    # Update search strategy with new potentially new results
                    # TODO: make the `wait` parameter changeable through UI (e.g., lazy vs greedy)
                    current_state = search_strategy.next(wait=False)

                    # Start worker to perform evaluation
                    experiment_params = eval_params.to_experiment_parameters(current_state.to_shallow_state())
                    worker_manager.start_experiment(experiment_params, current_state)

            except SequenceFinished:
                worker_manager.wait_until_all_evaluations_are_done()

                # Retry all tests with a dirty result once. Only once for JS engine subjects.
                if eval_params.subject_configuration.subject_type != 'js_engine' or i == 1:
                    self.retry_dirty_tests(eval_params, worker_manager)

                iteration_time = round(time.time() - start_time)
                logger.debug(
                    f'Last experiment has finished for iteration {i}/{nb_of_iterations}. This iteration took {iteration_time}s.'
                )

        worker_manager.wait_until_all_evaluations_are_done()
        self.state['reason'] = 'finished'
        self.__update_eval_queue(eval_params.experiment_name, 'done')
        Clients.push_notification_to_all(f'Evaluation of {experiment_name} has finished.')

    def retry_dirty_tests(self, eval_params: EvaluationParameters, worker_manager: WorkerManager) -> None:
        dirty_states = MongoDB().get_evaluated_states(eval_params, None, dirty=True)
        if (nb_of_dirty_states := len(dirty_states)) == 0:
            logger.info('No tests are associated with a dirty result.')
            return

        experiment = eval_params.experiment_name
        message = f'Retrying {nb_of_dirty_states} tests with a dirty result for {experiment}.'
        logger.info(message)

        Clients.push_notification_to_all(message)
        for dirty_state in dirty_states:
            if self.stop_gracefully or self.stop_forcefully:
                return
            experiment_params = eval_params.to_experiment_parameters(dirty_state.to_shallow_state())
            MongoDB().remove_datapoint(experiment_params)
            worker_manager.start_experiment(experiment_params, dirty_state)
        worker_manager.wait_until_all_evaluations_are_done()

        dirty_states_after_retry = MongoDB().get_evaluated_states(eval_params, None, dirty=True)
        logger.info(f'Dirty test results reduced from {nb_of_dirty_states} to {len(dirty_states_after_retry)}.')

    def run_single_experiment(self, params: ExperimentParameters) -> None:
        try:
            self.__update_state(is_running=True, reason='user', status='running')
            subject_config = params.subject_configuration
            state = params.state.to_deep_state(subject_config.subject_type, subject_config.subject_name)
            if not state.has_available_executable():
                Clients.push_notification_to_all(f'No available executable for state {state.commit_nb}.', type='error')
            else:
                worker_manager = WorkerManager(subject_config.subject_type, subject_config.subject_name, 1)
                worker_manager.start_experiment(params, state)
                Clients.push_complete_experiment_result(params)
        finally:
            # TODO: error handling
            self.__update_state(is_running=False, reason='idle', status='running')

    @staticmethod
    def create_sequence_strategy(eval_params: EvaluationParameters) -> SequenceStrategy:
        sequence_config = eval_params.sequence_configuration
        search_strategy = sequence_config.search_strategy
        sequence_limit = sequence_config.sequence_limit
        subject = factory.get_subject_from_params(eval_params.subject_configuration)
        state_factory = StateFactory(subject.state_oracle, eval_params)

        if search_strategy == 'bgb_sequence':
            strategy = BiggestGapBisectionSequence(state_factory, sequence_limit)
        elif search_strategy == 'bgb_search':
            strategy = BiggestGapBisectionSearch(state_factory)
        elif search_strategy == 'comp_search':
            strategy = CompositeSearch(state_factory, sequence_limit)
        else:
            raise UserError(f"Unknown search strategy option '{search_strategy}'")
        return strategy

    def activate_stop_gracefully(self):
        if self.state['is_running']:
            self.stop_gracefully = True
            self.__update_state(is_running=True, reason='user', status='waiting_to_stop')
            logger.info('Received user signal to gracefully stop.')
            Clients.push_notification_to_all('Waiting for all experiments to stop. No new experiments will be started.')
        else:
            logger.info('Received user signal to gracefully stop, but no evaluation is running.')

    def activate_stop_forcefully(self) -> None:
        if self.state['is_running']:
            self.stop_forcefully = True
            self.__update_state(is_running=True, reason='user', status='waiting_to_stop')
            WorkerManager.forcefully_stop_all_running_containers()
            logger.info('Received user signal to forcefully stop.')
            Clients.push_notification_to_all('Forcefully stopping all experiments. Sit tight!')
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
                update['logs'] = config.Loggers.get_logs()
            if arg == 'state' or all:
                self.state['nb_of_running_containers'] = WorkerManager.get_nb_of_running_worker_containers()
                update['state'] = self.state
        Clients.push_info(ws, update)

    def remove_datapoint(self, params: ExperimentParameters) -> None:
        MongoDB().remove_datapoint(params)
        Clients.push_results_to_all()

    def remove_cached_executable(self, subject_type: str, subject_name: str, state_name: str) -> None:
        ExecutableCache.remove_commit_executable_files(subject_type, subject_name, state_name)

    def __update_state(self, **kwargs) -> None:
        for key, value in kwargs.items():
            self.state[key] = value
        self.state['nb_of_running_containers'] = WorkerManager.get_nb_of_running_worker_containers()
        Clients.push_info_to_all({'state': self.state})

    def __init_eval_queue(self, eval_params_list: list[EvaluationParameters]) -> None:
        self.eval_queue = []
        for eval_params in eval_params_list:
            self.eval_queue.append(
                {
                    'experiment': eval_params.experiment_name,
                    'state': 'pending',
                }
            )

    def __update_eval_queue(self, experiment: str, state: str) -> None:
        for eval in self.eval_queue:
            if eval['experiment'] == experiment:
                eval['state'] = state
                return
