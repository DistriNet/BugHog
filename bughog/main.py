import logging
import os
import time

import bughog.database.mongo.container as mongodb_container
import bughog.version_control.revision_parser.bughog as bughog_commit_pos
from bughog.configuration import Global, Loggers
from bughog.database.mongo.mongodb import MongoDB, ServerException
from bughog.distribution.worker_manager import WorkerManager
from bughog.parameters import (
    DatabaseParameters,
    EvaluationParameters,
)
from bughog.search_strategy.bgb_search import BiggestGapBisectionSearch
from bughog.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bughog.search_strategy.composite_search import CompositeSearch
from bughog.search_strategy.sequence_strategy import SequenceFinished, SequenceStrategy
from bughog.subject import factory
from bughog.subject.web_browser.state_cache import PublicBrowserStateCache
from bughog.version_control.state.base import State
from bughog.version_control.state_factory import StateFactory
from bughog.web.clients import Clients

logger = logging.getLogger(__name__)


class Main:
    def __init__(self) -> None:
        self.state = {"is_running": False, "reason": "init", "status": "idle"}

        self.stop_gracefully = False
        self.stop_forcefully = False

        self.eval_queue = []

        self.db_connection_params = Global.get_database_params()
        self.connect_to_database(self.db_connection_params)
        PublicBrowserStateCache.update()
        bughog_commit_pos.update_commit_pos_data()
        factory.initialize_all_subject_folders()

        logger.info("BugHog is ready!")
        if os.getenv('GITHUB_TOKEN') is None:
            logger.warning('GITHUB_TOKEN was not configured in ./config/.env. This might result in failed API requests.')

    def connect_to_database(self, db_connection_params: DatabaseParameters) -> None:
        try:
            MongoDB().connect(db_connection_params)
        except ServerException:
            logger.error("Could not connect to database.", exc_info=True)

    def run(self, eval_params_list: list[EvaluationParameters]) -> None:
        # Sequence_configuration settings are the same over evaluation parameters (quick fix)
        self.__update_state(is_running=True, reason="user", status="running")
        worker_manager = WorkerManager(eval_params_list[0])
        self.stop_gracefully = False
        self.stop_forcefully = False
        try:
            self.__init_eval_queue(eval_params_list)
            for eval_params in eval_params_list:
                if self.stop_gracefully or self.stop_forcefully:
                    break
                self.__update_eval_queue(eval_params.evaluation_range.experiment_name, "active")
                self.__update_state(is_running=True, reason="user", status="running", queue=self.eval_queue)
                self.run_single_evaluation(eval_params, worker_manager)

        except Exception as e:
            logger.critical("A critical error occurred", exc_info=True)
            raise e
        finally:
            # Gracefully exit
            if self.stop_gracefully:
                logger.info("Gracefully stopping experiment queue due to user end signal...")
                self.state["reason"] = "user"
            if self.stop_forcefully:
                logger.info("Forcefully stopping experiment queue due to user end signal...")
                self.state["reason"] = "user"
                worker_manager.forcefully_stop_all_running_containers()
            else:
                logger.info("Gracefully stopping experiment queue since last experiment started.")
            # MongoDB.disconnect()
            logger.info("Waiting for remaining experiments to stop...")
            worker_manager.wait_until_all_evaluations_are_done()
            logger.info("BugHog has finished the evaluation!")
            self.__update_state(is_running=False, status="idle", queue=self.eval_queue)

    def run_single_evaluation(self, eval_params: EvaluationParameters, worker_manager: WorkerManager) -> None:
        # Quick fix: we attempt a couple of retries for each evaluation, to make sure pinpointing is comprehensive.
        # TODO: Pinpoint the issue that causes pinpointing to be incomprehensive. Presumably, this is caused by not all
        # states being evaluated upon deciding for the next state to be evaluated.
        nb_of_iterations = 3
        for i in range(1, nb_of_iterations + 1):
            start_time = time.time()
            browser_name = eval_params.subject_configuration.subject_name
            experiment_name = eval_params.evaluation_range.experiment_name
            search_strategy = self.create_sequence_strategy(eval_params)

            logger.info(f"Starting evaluation for experiment '{experiment_name}' with browser '{browser_name}', iteration {i}/{nb_of_iterations}.")
            try:
                while (self.stop_gracefully or self.stop_forcefully) is False:
                    # Update search strategy with new potentially new results
                    current_state = search_strategy.next()

                    # Start worker to perform evaluation
                    worker_manager.start_experiment(eval_params, current_state)

            except SequenceFinished:
                iteration_time = round(time.time() - start_time)
                worker_manager.wait_until_all_evaluations_are_done()
                logger.debug(f"Last experiment has finished for iteration {i}/{nb_of_iterations}. This iteration took {iteration_time}s.")

        # Retry all tests with a dirty result once.
        self.retry_dirty_tests(eval_params, worker_manager)

        self.state["reason"] = "finished"
        self.__update_eval_queue(eval_params.evaluation_range.experiment_name, "done")

    def retry_dirty_tests(self, eval_params: EvaluationParameters, worker_manager: WorkerManager) -> None:
        dirty_states = MongoDB().get_evaluated_states(eval_params, None, dirty=True)
        if (nb_of_dirty_states := len(dirty_states)) == 0:
            logger.info("No tests are associated with a dirty result.")
            return

        logger.info(f"Retrying {nb_of_dirty_states} tests with a dirty result...")
        for dirty_state in dirty_states:
            if self.stop_gracefully or self.stop_forcefully:
                return
            MongoDB().remove_datapoint(eval_params, dirty_state)
            worker_manager.start_experiment(eval_params, dirty_state)
        worker_manager.wait_until_all_evaluations_are_done()
        dirty_states_after_retry = MongoDB().get_evaluated_states(eval_params, None, dirty=True)
        logger.info(f"Dirty test results reduced from {nb_of_dirty_states} to {len(dirty_states_after_retry)}.")

    @staticmethod
    def create_sequence_strategy(eval_params: EvaluationParameters) -> SequenceStrategy:
        sequence_config = eval_params.sequence_configuration
        search_strategy = sequence_config.search_strategy
        sequence_limit = sequence_config.sequence_limit
        subject = factory.get_subject_from_params(eval_params)
        state_factory = StateFactory(subject.state_oracle, eval_params)

        if search_strategy == "bgb_sequence":
            strategy = BiggestGapBisectionSequence(state_factory, sequence_limit)
        elif search_strategy == "bgb_search":
            strategy = BiggestGapBisectionSearch(state_factory)
        elif search_strategy == "comp_search":
            strategy = CompositeSearch(state_factory, sequence_limit)
        else:
            raise AttributeError("Unknown search strategy option '%s'" % search_strategy)
        return strategy

    def activate_stop_gracefully(self):
        if self.state["is_running"]:
            self.stop_gracefully = True
            self.__update_state(is_running=True, reason="user", status="waiting_to_stop")
            logger.info("Received user signal to gracefully stop.")
        else:
            logger.info("Received user signal to gracefully stop, but no evaluation is running.")

    def activate_stop_forcefully(self) -> None:
        if self.state["is_running"]:
            self.stop_forcefully = True
            self.__update_state(is_running=True, reason="user", status="waiting_to_stop")
            WorkerManager.forcefully_stop_all_running_containers()
            logger.info("Received user signal to forcefully stop.")
        else:
            logger.info("Received user signal to forcefully stop, but no evaluation is running.")

    def quit_bughog(self) -> None:
        """
        Quits the bughog application, stopping all associated containers.
        """
        logger.info("Stopping all running BugHog containers...")
        self.activate_stop_forcefully()
        mongodb_container.stop()
        logger.info("Stopping BugHog core...")
        logging.shutdown()
        exit(0)

    def sigint_handler(self, sig_number, stack_frame) -> None:
        logger.debug(f"Sigint received with number {sig_number} for stack frame {stack_frame}")
        self.quit_bughog()

    def push_info(self, ws, *args) -> None:
        update = {}
        all = "all" in args
        for arg in args:
            if arg == "db_info" or all:
                update["db_info"] = MongoDB().get_info()
            if arg == "logs" or all:
                update["logs"] = Loggers.get_logs()
            if arg == "state" or all:
                update["state"] = self.state
        Clients.push_info(ws, update)

    def remove_datapoint(self, params: EvaluationParameters, state: State) -> None:
        MongoDB().remove_datapoint(params, state)
        Clients.push_results_to_all()

    def __update_state(self, **kwargs) -> None:
        for key, value in kwargs.items():
            self.state[key] = value
        Clients.push_info_to_all({"state": self.state})

    def __init_eval_queue(self, eval_params_list: list[EvaluationParameters]) -> None:
        self.eval_queue = []
        for eval_params in eval_params_list:
            self.eval_queue.append({"experiment": eval_params.evaluation_range.experiment_name, "state": "pending"})

    def __update_eval_queue(self, experiment: str, state: str) -> None:
        for eval in self.eval_queue:
            if eval["experiment"] == experiment:
                eval["state"] = state
                return
