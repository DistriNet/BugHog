import unittest
from typing import Callable, Optional
from unittest.mock import MagicMock

from bughog.parameters import EvaluationRange
from bughog.search_strategy.sequence_strategy import SequenceStrategy
from bughog.version_control.state_factory import StateFactory
from bughog.version_control.state.base import State, StateResult


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
        evaluated_indexes: Optional[list[int]] = None,
        outcome_func: Optional[Callable] = None) -> StateFactory:
        eval_params = MagicMock(spec=EvaluationConfiguration)
        eval_params.evaluation_range = MagicMock(spec=EvaluationRange)
        eval_params.evaluation_range.major_version_range = [0, 99]

        factory = MagicMock(spec=StateFactory)
        factory.__eval_params = eval_params
        factory.create_state = lambda index: TestSequenceStrategy.create_state(index, is_available, outcome_func)
        first_state = TestSequenceStrategy.create_state(0, is_available, outcome_func)
        last_state = TestSequenceStrategy.create_state(99, is_available, outcome_func)
        factory.boundary_states = (first_state, last_state)

        if evaluated_indexes:
            factory.create_evaluated_states = lambda: TestSequenceStrategy.get_states(evaluated_indexes, lambda _: True, outcome_func)
        else:
            factory.create_evaluated_states = lambda: []
        return factory

    @staticmethod
    def create_state(index, is_available: Callable, outcome_func: Optional[Callable]) -> State:
        state = MagicMock(spec=State)
        state.index = index
        state.has_available_binary = lambda: is_available(index)
        state.has_same_outcome = lambda x: State.has_same_outcome(state, x)
        state.has_dirty_or_no_result = lambda: State.has_dirty_or_no_result(state)
        state.result = StateResult([], [], [], False, outcome_func(index) if outcome_func else False)
        state.__eq__ = State.__eq__
        state.__repr__ = State.__repr__
        state.get_previous_and_next_state_with_binary = lambda: State.get_previous_and_next_state_with_binary(state)
        return state

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
        sequence_strategy = SequenceStrategy(state_factory, 0)
        state = sequence_strategy._find_closest_state_with_available_binary(state_factory.create_state(5), (state_factory.create_state(0), state_factory.create_state(10)))
        assert state is not None
        assert state.index == 5

    def test_find_closest_state_with_available_binary_2(self):
        state_factory = TestSequenceStrategy.create_state_factory(TestSequenceStrategy.only_has_binaries_for_even)
        sequence_strategy = SequenceStrategy(state_factory, 0)
        state = sequence_strategy._find_closest_state_with_available_binary(state_factory.create_state(5), (state_factory.create_state(0), state_factory.create_state(10)))
        assert state is not None
        assert state.index == 4

    def test_find_closest_state_with_available_binary_3(self):
        state_factory = TestSequenceStrategy.create_state_factory(TestSequenceStrategy.only_has_binaries_for_even)
        sequence_strategy = SequenceStrategy(state_factory, 0)
        state = sequence_strategy._find_closest_state_with_available_binary(state_factory.create_state(1), (state_factory.create_state(0), state_factory.create_state(2)))
        assert state is None
