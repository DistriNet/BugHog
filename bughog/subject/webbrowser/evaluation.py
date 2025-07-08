from bughog.subject.evaluation_framework import EvaluationFramework


class BrowserEvaluationFramework(EvaluationFramework):
    def experiment_is_valid(self, project: str, experiment: str) -> bool:
        dir_tree = self.evaluation_framework.dir_tree
        # Always runnable if there is either an interaction script or url_queue present
        if 'script' in data or 'url_queue' in data:
            return True

        # Should have exactly one main folder otherwise
        domains = dir_tree[project][experiment]
        main_paths = [paths for paths in domains.values() if paths is not None and 'main' in paths.keys()]
        if len(main_paths) != 1:
            return False
        # Main should have index.html
        if 'index.html' not in main_paths[0]['main'].keys():
            return False
        return True

    def create_empty_experiment(self, project: str, experiment: str):
        pass

    def get_default_file_content(self, file_type: str):
        pass
