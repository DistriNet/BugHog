import unittest

from bughog.search_strategy.bgb_search import BiggestGapBisectionSearch
from bughog.search_strategy.sequence_strategy import SequenceFinished
from test.sequence.test_sequence_strategy import TestSequenceStrategy as helper


class TestBiggestGapBisectionSearch(unittest.TestCase):

    def test_sbg_search_always_available_search(self):
        state_factory = helper.create_state_factory(
            helper.always_has_binary,
            outcome_func=lambda x: True if x < 50 else False)
        sequence = BiggestGapBisectionSearch(state_factory)
        index_sequence = [sequence.next(wait=False).index for _ in range(8)]
        assert index_sequence == [0, 99, 49, 74, 61, 55, 52, 50]
        self.assertRaises(SequenceFinished, lambda: sequence.next(wait=False))

    def test_sbg_search_even_available_search(self):
        state_factory = helper.create_state_factory(
            helper.only_has_binaries_for_even,
            outcome_func=lambda x: True if x < 35 else False)
        sequence = BiggestGapBisectionSearch(state_factory)

        assert sequence.next(wait=False).index == 0
        assert [state.index for state in sequence._considered_states] == [0]
        assert sequence._unavailability_gap_pairs == set()

        while True:
            try:
                sequence.next(wait=False)
            except SequenceFinished:
                break

        assert ([state.index for state in sequence._considered_states]
                == [0, 24, 30, 32, 34, 36, 48, 98])

        self.assertRaises(SequenceFinished, lambda: sequence.next(wait=False))
        assert {(first.index, last.index) for (first, last) in sequence._unavailability_gap_pairs} == {(34, 36)}


    def test_sbg_search_few_available_search(self):
        state_factory = helper.create_state_factory(
            helper.has_very_few_binaries,
            outcome_func=lambda x: True if x < 35 else False)
        sequence = BiggestGapBisectionSearch(state_factory)

        assert sequence.next(wait=False).index == 0
        assert [state.index for state in sequence._considered_states] == [0]
        assert sequence._unavailability_gap_pairs == set()

        assert sequence.next(wait=False).index == 99
        assert [state.index for state in sequence._considered_states] == [0, 99]

        assert sequence.next(wait=False).index == 44
        assert [state.index for state in sequence._considered_states] == [0, 44, 99]

        assert sequence.next(wait=False).index == 22
        assert [state.index for state in sequence._considered_states] == [0, 22, 44, 99]

        assert sequence.next(wait=False).index == 33
        assert [state.index for state in sequence._considered_states] == [0, 22, 33, 44, 99]

        self.assertRaises(SequenceFinished, lambda: sequence.next(wait=False))
        assert {(first.index, last.index) for (first, last) in sequence._unavailability_gap_pairs} == {(33, 44)}

    def test_sbg_search_few_available_search_complex(self):
        state_factory = helper.create_state_factory(
            helper.only_has_binaries_for_even,
            evaluated_indexes=[0, 12, 22, 34, 44, 56, 66, 78, 88, 98],
            outcome_func=lambda x: True if x < 35 or 66 < x else False)
        sequence = BiggestGapBisectionSearch(state_factory)

        while True:
            try:
                sequence.next(wait=False)
            except SequenceFinished:
                break

        assert ([state.index for state in sequence._considered_states]
                == [0, 12, 22, 34, 36, 38, 44, 56, 66, 68, 72, 78, 88, 98])

    def test_sbg_search_specific_error_case_1(self):
        state_factory = helper.create_state_factory(
            helper.always_has_binary,
            outcome_func=lambda x: True if x < 50 else False,
            error_func=lambda x: True if x in [49, 50, 51] else False)
        sequence = BiggestGapBisectionSearch(state_factory)
        index_sequence = [sequence.next(wait=False).index for _ in range(15)]
        assert index_sequence == [0, 99, 49, 74, 24, 36, 61, 42, 55, 45, 52, 47, 50, 48, 51]
        self.assertRaises(SequenceFinished, lambda: sequence.next(wait=False))

    def test_sbg_search_specific_error_case_2(self):
        state_factory = helper.create_state_factory(
            helper.always_has_binary,
            evaluated_indexes=[0, 48, 49, 50, 51, 52, 99],
            outcome_func=lambda x: True if x < 50 else False,
            error_func=lambda x: True if x in [49, 50, 51] else False,
            pending_func=lambda x: True if x in [48, 52] else False)
        sequence = BiggestGapBisectionSearch(state_factory)
        index_sequence = [sequence.next(wait=False).index for _ in range(11)]
        print(index_sequence)
        assert index_sequence == [24, 75, 36, 63, 42, 57, 45, 54, 46, 47, 53]
        self.assertRaises(SequenceFinished, lambda: sequence.next(wait=False))
