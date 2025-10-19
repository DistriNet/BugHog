import os
import re

from bughog.evaluation.file_structure import Folder
from bughog.subject.evaluation_framework import EvaluationFramework


class BrowserEvaluationFramework(EvaluationFramework):
    def experiment_is_runnable(self, experiment_folder: Folder) -> bool:
        return any(file.name in ('script.cmd', 'index.html') for file in experiment_folder.files)

    def fill_empty_experiment_with_default(self, path: str):
        file_path = os.path.join(path, 'index.html')
        with open(file_path, 'w') as file:
            file.write('<html></html>')

    def get_poc_file_name(self) -> str:
        return 'index.html'

    def get_comment_delimiter(self) -> str:
        return '<!--'

    def get_default_experiment_script(self, experiment_folder: Folder) -> list[str]:
        index_file_path = os.path.join(experiment_folder.path, 'index.html')
        if (domain := self.__get_domain(index_file_path)) is None:
            domain = 'a.test'
        project = experiment_folder.path.split('/')[5]
        experiment = experiment_folder.path.split('/')[6]
        url = f'https://{domain}/{project}/{experiment}/'
        return [f'navigate {url}']

    def get_default_file_content(self, file_type: str) -> bytes:
        default_file_path = os.path.join('/app/subject/web_browser/experiments/default_files/', file_type)
        if not os.path.isfile(default_file_path):
            return b''
        else:
            with open(default_file_path, 'rb') as file:
                return file.read()

    @staticmethod
    def __get_domain(file_path: str) -> str|None:
        with open(file_path, 'r') as file:
            content = file.read()
            match = re.match(r'bughog_domain: (.+)$', content, re.MULTILINE)
            return match[1].strip() if match else None
