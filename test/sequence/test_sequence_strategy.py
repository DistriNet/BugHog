import unittest
from typing import Callable
from unittest.mock import MagicMock

from bci.evaluations.logic import EvaluationConfiguration, EvaluationRange
from bci.evaluations.outcome_checker import OutcomeChecker
from bci.search_strategy.sequence_strategy import SequenceStrategy
from bci.version_control.factory import StateFactory
from bci.version_control.states.state import State


class TestSequenceStrategy(unittest.TestCase):

    '''
    Helper functions to create states and state factories for testing.
    '''

    @staticmethod
    def get_states(indexes: list[int], is_available, outcome_func) -> list[State]:
        return [TestSequenceStrategy.create_state(index, is_available, outcome_func) for index in indexes]

    @staticmethod
    def create_state_factory(
        is_available: Callable,
        evaluated_indexes: list[int] = None,
        outcome_func: Callable = None) -> StateFactory:
        eval_params = MagicMock(spec=EvaluationConfiguration)
        eval_params.evaluation_range = MagicMock(EvaluationRange)
        eval_params.evaluation_range.major_version_range = [0, 99]

        factory = StateFactory(eval_params, TestSequenceStrategy.create_outcome_checker(outcome_func))

        factory.create_state = lambda index: TestSequenceStrategy.create_state(index, is_available, outcome_func)
        if evaluated_indexes:
            factory.create_evaluated_states = lambda: TestSequenceStrategy.get_states(evaluated_indexes, lambda _: True, outcome_func)
        else:
            factory.create_evaluated_states = lambda: []
        return factory

    @staticmethod
    def create_state(index, is_available: Callable, outcome_func: Callable) -> State:
        state = MagicMock(spec=State)
        state.index = index
        state.has_available_binary = lambda: is_available(index)
        state.outcome = outcome_func(index) if outcome_func else None
        state.__eq__ = State.__eq__
        state.__repr__ = State.__repr__
        return state

    @staticmethod
    def create_outcome_checker(outcome_func: Callable) -> OutcomeChecker:
        if outcome_func:
            outcome_checker = MagicMock()
            outcome_checker.get_outcome = outcome_func
            return outcome_checker
        else:
            return None

    @staticmethod
    def always_has_binary(index) -> bool:
        return True

    @staticmethod
    def only_has_binaries_for_even(index) -> bool:
        return index % 2 == 0

    @staticmethod
    def has_very_few_binaries(index) -> bool:
        return index % 11 == 0

    @staticmethod
    def has_very_few_binaries_in_first_half(index) -> bool:
        if index < 50:
            return index % 22 == 0
        return True

    '''
    Actual tests
    '''

    def test_find_closest_state_with_available_binary_1(self):
        state_factory = TestSequenceStrategy.create_state_factory(TestSequenceStrategy.always_has_binary)
        sequence_strategy = SequenceStrategy(state_factory)
        state = sequence_strategy._find_closest_state_with_available_binary(state_factory.create_state(5), (state_factory.create_state(0), state_factory.create_state(10)))
        assert state.index == 5

    def test_find_closest_state_with_available_binary_2(self):
        state_factory = TestSequenceStrategy.create_state_factory(TestSequenceStrategy.only_has_binaries_for_even)
        sequence_strategy = SequenceStrategy(state_factory)
        state = sequence_strategy._find_closest_state_with_available_binary(state_factory.create_state(5), (state_factory.create_state(0), state_factory.create_state(10)))
        assert state.index == 6

    def test_find_closest_state_with_available_binary_3(self):
        state_factory = TestSequenceStrategy.create_state_factory(TestSequenceStrategy.only_has_binaries_for_even)
        sequence_strategy = SequenceStrategy(state_factory)
        state = sequence_strategy._find_closest_state_with_available_binary(state_factory.create_state(1), (state_factory.create_state(0), state_factory.create_state(2)))
        assert state is None
