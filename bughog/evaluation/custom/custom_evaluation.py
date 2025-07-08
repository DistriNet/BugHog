# import logging
# import os

# from bughog.configuration import Global
# from bughog.evaluation.collectors.collector import Collector, Type
# from bughog.evaluation.evaluation_framework import EvaluationFramework, FailedSanityCheck
# from bughog.evaluation.file_structure import Folder, parse_folder
# from bughog.parameters import ExperimentParameters, ExperimentResult
# from bughog.subject.executable import Executable
# from bughog.subject.webbrowser.interaction.interaction import BrowserInteraction
# from bughog.version_control.state_result_factory import StateResultFactory
# from bughog.web.clients import Clients

# logger = logging.getLogger(__name__)


# class CustomEvaluationFramework(EvaluationFramework):
#     def __init__(self):
#         super().__init__()
#         self.root_folder = parse_folder(Global.custom_page_folder)
#         self.initialize_experiments()

#     def initialize_experiments(self):
#         for project in self.root_folder.subfolders:
#             project.tags.append('project')

#             for experiment in project.subfolders:
#                 experiment.tags.append('experiment')
#                 if 'script.cmd' in [file.name for file in experiment.files]:
#                     experiment.tags.append('runnable')

#     def __get_project_folder(self, project_name: str) -> Folder:
#         for project in self.root_folder.subfolders:
#             if project.name == project_name:
#                 return project
#         raise Exception(f"Could not find project '{project_name}'")

#     def __get_experiment_folder(self, project_name: str, experiment_name: str) -> Folder:
#         project = self.__get_project_folder(project_name)
#         for experiment in project.subfolders:
#             if experiment.name == experiment_name:
#                 return experiment
#         raise Exception(f"Could not find experiment '{experiment_name}'")

#     def __get_interaction_script(self, project_name: str, experiment_name: str) -> list[str]:
#         experiment = self.__get_experiment_folder(project_name, experiment_name)
#         script_path = os.path.join(experiment.path, experiment.name, 'script.cmd')
#         if os.path.isfile(script_path):
#             # If an interaction script is specified, it is parsed and used
#             with open(script_path) as file:
#                 return file.readlines()
#         else:
#             raise Exception(f"Could not find experiment script at '{script_path}'")

#     # @staticmethod
#     # def is_runnable_experiment(project: str, poc: str, dir_tree: dict[str, dict], data: dict[str, str]) -> bool:
#     #     # Always runnable if there is either an interaction script or url_queue present
#     #     if 'script' in data or 'url_queue' in data:
#     #         return True

#     #     # Should have exactly one main folder otherwise
#     #     domains = dir_tree[project][poc]
#     #     main_paths = [paths for paths in domains.values() if paths is not None and 'main' in paths.keys()]
#     #     if len(main_paths) != 1:
#     #         return False
#     #     # Main should have index.html
#     #     if 'index.html' not in main_paths[0]['main'].keys():
#     #         return False
#     #     return True

#     def perform_specific_evaluation(self, executable: Executable, params: ExperimentParameters) -> ExperimentResult:
#         logger.info(f'Starting test for {params}')

#         state_result_factory = StateResultFactory(experiment=params.experiment)
#         collector = Collector([Type.REQUESTS, Type.LOGS])
#         collector.start()

#         is_dirty = False
#         tries_left = 3
#         script = self.__get_interaction_script(params.evaluation_configuration.project, params.experiment)
#         try:
#             sanity_check_was_successful = False
#             poc_was_reproduced = False
#             while not poc_was_reproduced and tries_left > 0:
#                 tries_left -= 1
#                 executable.pre_try_setup()
#                 BrowserInteraction(executable, script, params).execute()
#                 executable.post_try_cleanup()
#                 intermediary_state_result = state_result_factory.get_result(collector.collect_results())
#                 sanity_check_was_successful |= not intermediary_state_result.is_dirty
#                 poc_was_reproduced = intermediary_state_result.reproduced
#             if not poc_was_reproduced and not sanity_check_was_successful:
#                 raise FailedSanityCheck()
#         except FailedSanityCheck:
#             logger.error('Evaluation sanity check has failed', exc_info=True)
#             is_dirty = True
#         except Exception as e:
#             logger.error(f'An error during evaluation: {e}', exc_info=True)
#             is_dirty = True
#         finally:
#             logger.debug(f'Evaluation finished with {tries_left} tries left')
#             collector.stop()
#             results = collector.collect_results()
#         return params.create_test_result_with(executable.version, executable.origin, results, is_dirty)

#     def get_experiments(self, project: str) -> list[tuple[str, bool]]:
#         if project not in self.tests_per_project:
#             return []
#         pocs = [(poc_name, poc_data['runnable']) for poc_name, poc_data in self.tests_per_project[project].items()]
#         return sorted(pocs, key=lambda x: x[0])

#     def get_projects(self) -> list[str]:
#         return sorted(list(self.tests_per_project.keys()))

#     def create_empty_project(self, project_name: str):
#         self.is_valid_name(project_name)
#         if project_name in self.dir_tree:
#             raise AttributeError(f"The given project name '{project_name}' already exists.")

#         new_project_path = os.path.join(Global.custom_page_folder, project_name)
#         os.mkdir(new_project_path)
#         self.reload_experiments()

#     def get_poc_structure(self, project: str, poc: str) -> dict:
#         return self.dir_tree[project][poc]

#     def _get_poc_file_path(self, project: str, poc: str, domain: str, path: str, file_name: str) -> str:
#         # Top-level config file
#         if domain == 'Config' and path == '_':
#             return os.path.join(Global.custom_page_folder, project, poc, file_name)

#         return os.path.join(Global.custom_page_folder, project, poc, domain, path, file_name)

#     def get_poc_file(self, project: str, poc: str, domain: str, path: str, file_name: str) -> str:
#         file_path = self._get_poc_file_path(project, poc, domain, path, file_name)
#         if os.path.isfile(file_path):
#             with open(file_path) as file:
#                 return file.read()
#         raise AttributeError(f"Could not find PoC file at expected path '{file_path}'")

#     def update_poc_file(self, project: str, poc: str, domain: str, path: str, file_name: str, content: str) -> bool:
#         file_path = self._get_poc_file_path(project, poc, domain, path, file_name)
#         if os.path.isfile(file_path):
#             if content == '':
#                 logger.warning('Attempt to save empty file ignored')
#                 return False
#             with open(file_path, 'w') as file:
#                 file.write(content)
#             return True
#         return False

#     def create_empty_poc(self, project: str, poc_name: str):
#         self.is_valid_name(poc_name)
#         poc_path = os.path.join(Global.custom_page_folder, project, poc_name)
#         if os.path.exists(poc_path):
#             raise AttributeError(f"The given PoC name '{poc_name}' already exists.")

#         os.makedirs(poc_path)
#         self.reload_experiments()
#         Clients.push_experiments_to_all()

#     def add_page(self, project: str, poc: str, domain: str, path: str, file_type: str):
#         domain_path = os.path.join(Global.custom_page_folder, project, poc, domain)
#         if not os.path.exists(domain_path):
#             os.makedirs(domain_path)

#         self.is_valid_name(path)
#         if file_type == 'py':
#             file_name = path if path.endswith('.py') else path + '.py'
#             file_path = os.path.join(domain_path, file_name)
#         else:
#             page_path = os.path.join(domain_path, path)
#             if not os.path.exists(page_path):
#                 os.makedirs(page_path)
#             new_file_name = f'index.{file_type}'
#             file_path = os.path.join(page_path, new_file_name)
#             headers_file_path = os.path.join(page_path, 'headers.json')
#             if not os.path.exists(headers_file_path):
#                 with open(headers_file_path, 'w') as file:
#                     file.write(self.get_default_file_content('headers.json'))

#         if os.path.exists(file_path):
#             raise AttributeError(f"The given page '{path}' does already exist.")
#         with open(file_path, 'w') as file:
#             file.write(self.get_default_file_content(file_type))

#         self.reload_experiments()
#         # Notify clients of change (an experiment might now be runnable)
#         Clients.push_experiments_to_all()

#     def add_config(self, project: str, poc: str, type: str) -> bool:
#         content = self.get_default_file_content(type)

#         if content == '':
#             return False

#         file_path = os.path.join(Global.custom_page_folder, project, poc, type)
#         with open(file_path, 'w') as file:
#             file.write(content)

#         self.reload_experiments()
#         # Notify clients of change (an experiment might now be runnable)
#         Clients.push_experiments_to_all()

#         return True

#     @staticmethod
#     def get_default_file_content(file_type: str) -> str:
#         path = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'default_files/{file_type}')

#         if not os.path.exists(path):
#             return ''

#         with open(path, 'r') as file:
#             return file.read()

#     def reload_experiments(self):
#         self.root_folder = parse_folder(Global.custom_page_folder)
#         self.initialize_experiments()
#         logger.info('Experiments are reloaded.')
