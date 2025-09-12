import logging
import os
import time

from bughog.database.mongo.mongodb import MongoDB
from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.experiment_result import ExperimentResult
from bughog.evaluation.interaction import Interaction
from bughog.parameters import EvaluationParameters
from bughog.subject import factory
from bughog.subject.executable import Executable, ExecutableStatus
from bughog.subject.simulation import Simulation
from bughog.version_control.state.base import State

logger = logging.getLogger(__name__)


class Evaluation:
    def __init__(self, subject_type: str):
        self.subject_type = subject_type
        self.experiments = factory.create_experiments(subject_type)
        self.should_stop = False

    def evaluate(self, params: EvaluationParameters, state: State, is_worker=False):
        if MongoDB().has_result(params, state):
            logger.warning(f"Experiment '{params.evaluation_range.experiment_name}' for '{state}' was already performed, skipping.")
            return

        subject = factory.get_subject_from_params(params)

        experiment_folder = self.experiments.get_experiment_folder(params)
        executable = subject.create_executable(params.subject_configuration, state)
        runtime_flags = self.experiments.framework.get_runtime_flags(experiment_folder)
        runtime_env_vars = self.experiments.framework.get_runtime_env_vars(experiment_folder)
        runtime_args = self.experiments.framework.get_runtime_args(experiment_folder)

        collector = subject.create_result_collector()

        if regex := self.experiments.framework.get_expected_output_regex(experiment_folder):
            collector.set_expected_output_regex(regex)
        if regex := self.experiments.framework.get_unexpected_output_regex(experiment_folder):
            collector.set_unexpected_output_regex(regex)

        executable.add_runtime_flags(runtime_flags)
        executable.add_runtime_env_vars(runtime_env_vars)
        executable.add_runtime_args(runtime_args)

        simulation = subject.create_simulation(executable, experiment_folder, params)
        script = self.experiments.get_interaction_script(experiment_folder)

        if self.should_stop:
            self.should_stop = False
            return
        try:
            executable.pre_experiment_setup()
            result = self.conduct_experiment(executable, simulation, collector, script)
            MongoDB().store_result(params, result)
        except Exception as e:
            executable.status = ExecutableStatus.EXPERIMENT_FAILED
            if is_worker:
                raise e
            else:
                logger.error('An error occurred during experiment', exc_info=True)
        finally:
            executable.post_experiment_cleanup()

    def conduct_experiment(self, executable: Executable, simulation: Simulation, collector: Collector, script: list[str]) -> ExperimentResult:
        is_dirty = False
        tries_left = 3
        collector.start()
        poc_was_reproduced = False
        intermediary_variables = None

        # Perform experiment with retries
        logger.info(f'Starting experiment for {executable.state}.')
        start_time = time.time()
        while not poc_was_reproduced and tries_left > 0:
            tries_left -= 1
            executable.pre_try_setup()
            try:
                Interaction(script).do_experiment(simulation)
            except Exception as e:
                logger.error(f'An error during the experiment: {e}', exc_info=True)
                is_dirty = True
            executable.post_try_cleanup()
            _, intermediary_variables = collector.collect_results()
            poc_was_reproduced = ExperimentResult.poc_is_reproduced(intermediary_variables)
        collector.stop()
        raw_results, result_variables = collector.collect_results()

        # Perform sanity check if not reproduced and potential in-poc sanity check did not succeed
        if self.experiments.framework.requires_sanity_check() and (intermediary_variables is None or ExperimentResult.poc_is_dirty(intermediary_variables)):
            collector.start()
            try:
                Interaction(script).do_sanity_check(simulation)
            except Exception as e:
                logger.error(f'An error during the sanity check: {e}', exc_info=True)
            collector.stop()
            _, sanity_check_variables = collector.collect_results()
            if not ExperimentResult.poc_passed_sanity_check(sanity_check_variables):
                is_dirty = True
            result_variables.update(sanity_check_variables)

        elapsed_time = time.time() - start_time
        logger.info(f'Experiment for {executable.state} finished in {elapsed_time:.2f}s with {tries_left} tries left.')
        return ExperimentResult(executable.version, executable.origin, executable.state.to_dict(), raw_results, result_variables, is_dirty)

    @staticmethod
    def get_default_file_content(file_type: str) -> str:
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'default_files/{file_type}')

        if not os.path.exists(path):
            return ''

        with open(path, 'r') as file:
            return file.read()

    def stop_gracefully(self):
        self.should_stop = True


class FailedSanityCheck(Exception):
    pass
