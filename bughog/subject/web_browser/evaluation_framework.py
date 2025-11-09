import os

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

    def get_default_experiment_script(self, experiment_folder: Folder) -> list[str]:
        poc_file = experiment_folder.get_file('index.html')
        domain = poc_file.get_bughog_poc_parameter('domain') or 'a.test'
        project = experiment_folder.path.split('/')[5]
        experiment = experiment_folder.path.split('/')[6]
        url = f'https://{domain}/{project}/{experiment}/'
        return [f'navigate {url}']
