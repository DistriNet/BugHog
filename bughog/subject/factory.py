from functools import lru_cache

from bughog.evaluation.collectors.requests import RequestCollector
from bughog.evaluation.experiment import Experiments
from bughog.parameters import EvaluationParameters
from bughog.subject.base import Subject
from bughog.subject.evaluation_framework import EvaluationFramework
from bughog.subject.state_oracle import StateOracle
from bughog.subject.webbrowser.chromium.subject import Chromium
from bughog.subject.webbrowser.evaluation import BrowserEvaluationFramework
from bughog.subject.webbrowser.firefox.subject import Firefox
from bughog.version_control.state.release.base import ReleaseState

subjects = {
    'js_engine': {
        'collectors': [],
        'subjects': []
    },
    'web_browser': {
        'collectors': [
            RequestCollector
        ],
        'evaluation_framework': BrowserEvaluationFramework,
        'subjects': [
            Chromium,
            Firefox,
        ]
    }
}


@staticmethod
def get_all_subject_types() -> list[str]:
    return sorted(subjects.keys())


@staticmethod
def get_all_subjects_for(subject_type: str) -> list[type[Subject]]:
    if subject_classes := subjects.get(subject_type):
        return subject_classes['subjects']
    raise AttributeError(f"Subject type '{subject_type}' is not supported.")


@staticmethod
def get_all_subject_names_for(subject_type: str) -> list[str]:
    return [subject.name() for subject in get_all_subjects_for(subject_type)]


@staticmethod
def create_evaluation_framework(subject_type: str) -> EvaluationFramework:
    if subject_classes := subjects.get(subject_type):
        return subject_classes['evaluation_framework'](subject_type)
    raise AttributeError(f"Subject type '{subject_type}' is not supported.")


@lru_cache(maxsize=10)
def create_experiments(subject_type: str) -> Experiments:
    return Experiments(subject_type, create_evaluation_framework(subject_type))


@staticmethod
def create_subject(params: EvaluationParameters) -> Subject:
    type = params.subject_configuration.subject_type
    name = params.subject_configuration.subject_name
    return get_subject_class(type)(name)


@staticmethod
def get_subject_availability() -> list[dict]:
    subject_availability = []
    for subject_type in get_all_subject_types():
        subjects_for_type = {'subject_type': subject_type, 'subjects': []}
        for subject in get_all_subjects_for(subject_type):
            subjects_for_type['subjects'].append(subject.get_availability())
        subject_availability.append(subjects_for_type)
    return subject_availability


@staticmethod
def get_subject_availability_for(type: str, name: str) -> dict:
    return get_subject_class(type, name).get_availability()


@staticmethod
def get_subject_class(subject_type: str, subject_name: str) -> type[Subject]:
    if available_subjects := subjects.get(subject_type):
        if subject_class := available_subjects.get(subject_name):
            return subject_class
    raise AttributeError(f"Subject '{subject_type} {subject_name}' is not supported.")


@staticmethod
def get_release_state_class(subject_type: str, subject_name: str) -> type[ReleaseState]:
    return get_subject_class(subject_type, subject_name).release_state_class()


@staticmethod
def get_state_oracle(subject_type: str, subject_name: str) -> type[StateOracle]:
    return get_subject_class(subject_type, subject_name).state_oracle()
