from typing import Optional
from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class BrowserEvaluationFramework(EvaluationFramework):
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        if 'script.cmd' in [file.name for file in experiment_folder.files]:
            return True

        # If an experiment has no script.cmd, it should have exactly one main page.
        return self.__find_only_main_page(experiment_folder) is not None

    def fill_empty_experiment_with_default(self, path: str):
        pass

    def get_poc_file_name(self) -> str:
        return 'index.html'

    def get_comment_delimiter(self) -> str:
        return '<!--'

    def get_default_experiment_script(self, experiment_folder: Folder) -> list[str]:
        if main_folder := self.__find_only_main_page(experiment_folder):
            project = main_folder.path.split('/')[-4]
            experiment = main_folder.path.split('/')[-3]
            domain = main_folder.path.split('/')[-2]
            url = f'https://{domain}/{project}/{experiment}/main/'
            return [f'navigate {url}']
        return ['navigate']

    def get_default_file_content(self, file_type: str):
        pass

    def __find_only_main_page(self, experiment_folder: Folder) -> Optional[Folder]:
        main_folder = None
        for domain_folder in experiment_folder.subfolders:
            for path_folder in domain_folder.subfolders:
                if path_folder.name == 'main':
                    if main_folder is None:
                        main_folder = path_folder
                    else:
                        return None
        return main_folder

