from functools import lru_cache

from bughog.evaluation.experiments import Experiments
from bughog.parameters import EvaluationParameters
from bughog.subject.evaluation_framework import EvaluationFramework
from bughog.subject.js_engine.evaluation_framework import JSEngineEvaluationFramework
from bughog.subject.js_engine.v8.subject import V8Subject
from bughog.subject.subject import Subject
from bughog.subject.web_browser.chromium.subject import Chromium
from bughog.subject.web_browser.evaluation import BrowserEvaluationFramework
from bughog.subject.web_browser.firefox.subject import Firefox

subjects = {
    'js_engine': {
        'evaluation_framework': JSEngineEvaluationFramework,
        'subjects': [
            V8Subject()
        ]
    },
    'web_browser': {
        'evaluation_framework': BrowserEvaluationFramework,
        'subjects': [
            Chromium(),
            Firefox(),
        ],
    },
}


@staticmethod
def get_all_subject_types() -> list[str]:
    return sorted(subjects.keys())


@staticmethod
def get_all_subjects_for(subject_type: str) -> list[Subject]:
    if subject_objects := subjects.get(subject_type):
        return subject_objects['subjects']
    raise AttributeError(f"Subject type '{subject_type}' is not supported.")


@staticmethod
def get_all_subject_names_for(subject_type: str) -> list[str]:
    return [subject.name for subject in get_all_subjects_for(subject_type)]


@staticmethod
def create_evaluation_framework(subject_type: str) -> EvaluationFramework:
    if subject_classes := subjects.get(subject_type):
        return subject_classes['evaluation_framework'](subject_type)
    raise AttributeError(f"Subject type '{subject_type}' is not supported.")


@lru_cache(maxsize=10)
def create_experiments(subject_type: str) -> Experiments:
    return Experiments(subject_type, create_evaluation_framework(subject_type))


@staticmethod
def invalidate_experiment_cache():
    create_experiments.cache_clear()


@staticmethod
def get_all_subject_availability() -> list[dict]:
    subject_availability = []
    for subject_type in get_all_subject_types():
        subjects_for_type = {'subject_type': subject_type, 'subjects': []}
        for subject in get_all_subjects_for(subject_type):
            subjects_for_type['subjects'].append(subject.get_availability())
        subject_availability.append(subjects_for_type)
    return subject_availability


@staticmethod
def get_subject_availability(subject_type: str, subject_name: str) -> tuple[int,int]:
    subject_availability = get_subject(subject_type, subject_name).get_availability()
    return subject_availability['min_version'], subject_availability['max_version']


@staticmethod
def get_subject_from_params(params: EvaluationParameters) -> Subject:
    subject_type = params.subject_configuration.subject_type
    subject_name = params.subject_configuration.subject_name
    return get_subject(subject_type, subject_name)


@staticmethod
def get_subject(subject_type: str, subject_name: str) -> Subject:
    subjects = get_all_subjects_for(subject_type)
    matched_subjects = [subject for subject in subjects if subject.name == subject_name]
    if len(matched_subjects) > 0:
        return matched_subjects[0]
    raise AttributeError(f"Subject '{subject_type}, {subject_name}' is not supported.")
