import logging
import os

from bughog.configuration import Global
from bughog.database.mongo.mongodb import MongoDB
from bughog.evaluation.collectors.collector import Collector
from bughog.evaluation.experiment_result import ExperimentResult
from bughog.evaluation.interaction import Interaction
from bughog.parameters import EvaluationParameters
from bughog.subject import factory
from bughog.subject.executable import Executable, ExecutableStatus
from bughog.subject.simulation import Simulation
from bughog.version_control.state.base import State
from bughog.web.clients import Clients

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

        collector = subject.create_result_collector()

        if regex := self.experiments.framework.get_expected_output_regex(experiment_folder):
            collector.set_expected_output_regex(regex)
        if regex := self.experiments.framework.get_unexpected_output_regex(experiment_folder):
            collector.set_unexpected_output_regex(regex)

        executable.add_runtime_flags(runtime_flags)
        executable.add_runtime_env_vars(runtime_env_vars)
        executable.pre_evaluation_setup()

        simulation = subject.create_simulation(executable, experiment_folder, params)
        script = self.experiments.get_interaction_script(experiment_folder)

        if self.should_stop:
            self.should_stop = False
            return
        try:
            executable.pre_experiment_setup()
            logger.info(f'Starting test for {params}')
            result = self.conduct_experiment(executable, simulation, collector, script)
            MongoDB().store_result(params, result)
            logger.info(f'Experiment finalized: {params}')
        except Exception as e:
            executable.status = ExecutableStatus.EXPERIMENT_FAILED
            if is_worker:
                raise e
            else:
                logger.error('An error occurred during evaluation', exc_info=True)
        finally:
            executable.post_experiment_cleanup()

        executable.post_evaluation_cleanup()
        logger.debug('Evaluation finished')

    def conduct_experiment(self, executable: Executable, simulation: Simulation, collector: Collector, script: list[str]) -> ExperimentResult:
        is_dirty = False
        tries_left = 3
        collector.start()
        poc_was_reproduced = False

        # Perform experiment with retries
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

        # Perform sanity check if not reproduced
        if not poc_was_reproduced:
            collector.start()
            try:
                Interaction(script).do_sanity_check(simulation)
            except Exception as e:
                logger.error(f'An error during the sanity check: {e}', exc_info=True)
            collector.stop()
            _, sanity_check_variables = collector.collect_results()
            if ExperimentResult.poc_is_dirty(sanity_check_variables):
                is_dirty = True

        logger.debug(f'Evaluation finished with {tries_left} tries left')
        return ExperimentResult(executable.version, executable.origin, executable.state.to_dict(), raw_results, result_variables, is_dirty)

    def update_poc_file(self, project: str, poc: str, domain: str, path: str, file_name: str, content: str) -> bool:
        file_path = self._get_poc_file_path(project, poc, domain, path, file_name)
        if os.path.isfile(file_path):
            if content == '':
                logger.warning('Attempt to save empty file ignored')
                return False
            with open(file_path, 'w') as file:
                file.write(content)
            return True
        return False

    def create_empty_poc(self, project: str, poc_name: str):
        self.is_valid_name(poc_name)
        poc_path = os.path.join(Global.custom_page_folder, project, poc_name)
        if os.path.exists(poc_path):
            raise AttributeError(f"The given PoC name '{poc_name}' already exists.")

        os.makedirs(poc_path)
        self.reload_experiments()
        Clients.push_experiments_to_all()

    def add_page(self, project: str, poc: str, domain: str, path: str, file_type: str):
        domain_path = os.path.join(Global.custom_page_folder, project, poc, domain)
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)

        self.is_valid_name(path)
        if file_type == 'py':
            file_name = path if path.endswith('.py') else path + '.py'
            file_path = os.path.join(domain_path, file_name)
        else:
            page_path = os.path.join(domain_path, path)
            if not os.path.exists(page_path):
                os.makedirs(page_path)
            new_file_name = f'index.{file_type}'
            file_path = os.path.join(page_path, new_file_name)
            headers_file_path = os.path.join(page_path, 'headers.json')
            if not os.path.exists(headers_file_path):
                with open(headers_file_path, 'w') as file:
                    file.write(self.get_default_file_content('headers.json'))

        if os.path.exists(file_path):
            raise AttributeError(f"The given page '{path}' does already exist.")
        with open(file_path, 'w') as file:
            file.write(self.get_default_file_content(file_type))

        self.reload_experiments()
        # Notify clients of change (an experiment might now be runnable)
        Clients.push_experiments_to_all()

    def add_config(self, project: str, poc: str, type: str) -> bool:
        content = self.get_default_file_content(type)

        if content == '':
            return False

        file_path = os.path.join(Global.custom_page_folder, project, poc, type)
        with open(file_path, 'w') as file:
            file.write(content)

        self.reload_experiments()
        # Notify clients of change (an experiment might now be runnable)
        Clients.push_experiments_to_all()

        return True

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
