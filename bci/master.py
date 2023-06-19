import logging

from dotenv import load_dotenv

from analysis.plot_factory import PlotFactory
from bci.configuration import Global
from bci.database.mongo.mongodb import MongoDB, ServerException
from bci.distribution.worker_manager import WorkerManager
from bci.evaluations.custom.custom_evaluation import CustomEvaluationFramework
from bci.evaluations.evaluation_framework import EvaluationFramework
from bci.evaluations.logic import (DatabaseConnectionParameters,
                                   EvaluationParameters, PlotParameters,
                                   SequenceConfiguration, WorkerParameters)
from bci.evaluations.outcome_checker import OutcomeChecker
from bci.evaluations.samesite.samesite_evaluation import \
    SameSiteEvaluationFramework
from bci.evaluations.xsleaks.evaluation import XSLeaksEvaluation
from bci.search_strategy.composite_search import CompositeSearch
from bci.search_strategy.n_ary_search import NArySearch
from bci.search_strategy.n_ary_sequence import NArySequence, SequenceFinished
from bci.search_strategy.sequence_strategy import SequenceStrategy
from bci.version_control import state_factory
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)


class Master:

    def __init__(self):
        self.running = False

        self.stop_gracefully = False
        self.stop_forcefully = False

        self.evaluations = []
        self.evaluation_framework = None
        self.worker_manager = None
        self.available_evaluation_frameworks = {}

        self.firefox_build = None
        self.chromium_build = None

        load_dotenv()

        Global.initialize_folders()
        self.db_connection_params = Global.get_database_connection_params()
        self.connect_to_database(self.db_connection_params)
        self.inititialize_available_evaluation_frameworks()
        logger.info("BugHog is ready!")

    def connect_to_database(self, db_connection_params: DatabaseConnectionParameters):
        try:
            MongoDB.connect(db_connection_params)
        except ServerException:
            logger.error("Could not connect to database.", exc_info=True)

    def run(self, eval_params: EvaluationParameters):
        self.running = True
        self.stop_gracefully = False
        self.stop_forcefully = False

        browser_config = eval_params.browser_configuration
        evaluation_config = eval_params.evaluation_configuration
        evaluation_range = eval_params.evaluation_range
        sequence_config = eval_params.sequence_configuration

        logger.info(f'Running experiments for {browser_config.browser_name} ({", ".join(evaluation_range.mech_groups)})')
        self.evaluation_framework = self.get_specific_evaluation_framework(
            evaluation_config.project
        )
        worker_manager = WorkerManager(sequence_config.nb_of_containers)

        try:
            state_list = state_factory.get_state_list(browser_config, evaluation_range)

            search_strategy = self.parse_search_strategy(
                sequence_config.search_strategy, state_list, 2, sequence_config.sequence_limit
            )

            outcome_checker = OutcomeChecker(sequence_config)

            # The state_lineage is put into self.evaluation as a means to check on the process through front-end
            self.evaluations.append(state_list)

            try:
                current_state = search_strategy.next()
                while (self.stop_gracefully or self.stop_forcefully) is False:
                    worker_params = eval_params.create_worker_params_for(current_state, self.db_connection_params)

                    # Callback function for sequence strategy
                    update_outcome = self.get_update_outcome_cb(search_strategy, worker_params, sequence_config, outcome_checker)

                    # Check whether state is already evaluated
                    if self.evaluation_framework.has_all_results(worker_params):
                        logger.info(f"State '{current_state.revision_number}' already evaluated.")
                        update_outcome()
                        current_state = search_strategy.next()
                        continue

                    # Start worker to perform evaluation
                    worker_manager.start_test(worker_params, update_outcome)

                    current_state = search_strategy.next()
            except SequenceFinished:
                logger.debug("Last experiment has started")

        except Exception as e:
            logger.critical("A critical error occurred", exc_info=True)
            raise e
        finally:
            # Gracefully exit
            if self.stop_gracefully:
                logger.info("Gracefully stopping experiment queue due to user end signal...")
            if self.stop_forcefully:
                logger.info("Forcefully stopping experiment queue due to user end signal...")
                worker_manager.forcefully_stop_all_running_containers()
            else:
                logger.info("Gracefully stopping experiment queue since last experiment started.")
            # MongoDB.disconnect()
            logger.info("Waiting for remaining experiments to stop...")
            worker_manager.wait_until_all_evaluations_are_done()
            logger.info("BugHog has finished the evaluation!")
            self.running = False

    @staticmethod
    def get_update_outcome_cb(search_strategy: SequenceStrategy, worker_params: WorkerParameters, sequence_config: SequenceConfiguration, checker: OutcomeChecker) -> None:
        def cb():
            if sequence_config.target_mech_id is not None and len(worker_params.mech_groups) == 1:
                result = MongoDB.get_instance().get_result(worker_params.create_test_params_for(worker_params.mech_groups[0]))
                outcome = checker.get_outcome(result)
                search_strategy.update_outcome(worker_params.state, outcome)
        return cb

    def inititialize_available_evaluation_frameworks(self):
        self.available_evaluation_frameworks["samesite"] = SameSiteEvaluationFramework()
        self.available_evaluation_frameworks["custom"] = CustomEvaluationFramework()
        self.available_evaluation_frameworks["xsleaks"] = XSLeaksEvaluation()

    @staticmethod
    def parse_search_strategy(search_strategy_option: str, state_list: list[State], n: int, sequence_limit: int):
        if search_strategy_option == "bin_seq":
            return NArySequence(state_list, n, limit=sequence_limit)
        if search_strategy_option == "bin_search":
            return NArySearch(state_list, n)
        if search_strategy_option == "comp_search":
            return CompositeSearch(state_list, n, sequence_limit, NArySequence, NArySearch)
        raise AttributeError("Unknown search strategy option '%s'" % search_strategy_option)

    def get_specific_evaluation_framework(self, evaluation_name: str) -> EvaluationFramework:
        # TODO: we always use 'custom', in which evaluation_name is a project
        evaluation_name = 'custom'
        if evaluation_name not in self.available_evaluation_frameworks.keys():
            raise AttributeError("Could not find a framework for '%s'" % evaluation_name)
        return self.available_evaluation_frameworks[evaluation_name]

    def activate_stop_gracefully(self):
        if self.evaluation_framework:
            self.stop_gracefully = True
            self.evaluation_framework.stop_gracefully()
            logger.info("Received user signal to gracefully stop.")
        else:
            logger.info("Received user signal to gracefully stop, but no evaluation is running.")

    def activate_stop_forcefully(self):
        if self.evaluation_framework:
            self.stop_forcefully = True
            self.evaluation_framework.stop_gracefully()
            logger.info("Received user signal to forcefully stop.")
        else:
            logger.info("Received user signal to forcefully stop, but no evaluation is running.")

    def get_html_plot(self, params: PlotParameters) -> tuple[str, int]:
        return PlotFactory.create_html_plot_string(params, MongoDB.get_instance())
