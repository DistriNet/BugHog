import unittest

from bci.search_strategy.composite_search import CompositeSearch
from bci.search_strategy.sequence_strategy import SequenceFinished
from test.sequence.test_sequence_strategy import TestSequenceStrategy as helper


class TestCompositeSearch(unittest.TestCase):

    def test_binary_sequence_always_available_composite(self):
        state_factory = helper.create_state_factory(
            helper.always_has_binary,
            outcome_func=lambda x: True if x < 50 else False)
        sequence = CompositeSearch(state_factory, 10)

        # Sequence
        index_sequence = [sequence.next().index for _ in range(10)]
        assert index_sequence == [0, 99, 49, 74, 24, 36, 61, 86, 12, 42]

        # Simulate that the previous part of the evaluation has been completed
        state_factory = helper.create_state_factory(
            helper.always_has_binary,
            outcome_func=lambda x: True if x < 50 else False,
            evaluated_indexes=[0, 99, 49, 74, 24, 36, 61, 86, 12, 42]
        )

        # Sequence
        index_sequence = [sequence.next().index for _ in range(3)]
        assert index_sequence == [55, 52, 50]

        self.assertRaises(SequenceFinished, sequence.next)

    def test_binary_sequence_always_available_composite_two_shifts(self):
        state_factory = helper.create_state_factory(
            helper.always_has_binary,
            outcome_func=lambda x: True if x < 33 or 81 < x else False)
        sequence = CompositeSearch(state_factory, 10)

        # Sequence
        index_sequence = [sequence.next().index for _ in range(10)]
        assert index_sequence == [0, 99, 49, 74, 24, 36, 61, 86, 12, 42]

        # Simulate that the previous part of the evaluation has been completed
        state_factory = helper.create_state_factory(
            helper.always_has_binary,
            outcome_func=lambda x: True if x < 33 or 81 < x else False,
            evaluated_indexes=[0, 99, 49, 74, 24, 36, 61, 86, 12, 42]
        )

        while True:
            try:
                print(sequence.next())
            except SequenceFinished:
                break

        assert sequence.search_strategy is not None
        evaluated_indexes = [state.index for state in sequence.search_strategy._completed_states]

        assert sequence.search_strategy is not None
        assert 32 in evaluated_indexes
        assert 33 in evaluated_indexes
        assert 81 in evaluated_indexes
        assert 82 in evaluated_indexes

        assert 1 not in evaluated_indexes
        assert 13 not in evaluated_indexes
        assert 37 not in evaluated_indexes
        assert 50 not in evaluated_indexes
        assert 62 not in evaluated_indexes
        assert 87 not in evaluated_indexes
