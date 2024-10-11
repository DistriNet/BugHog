import unittest

from bci.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bci.search_strategy.sequence_strategy import SequenceFinished
from test.sequence.test_sequence_strategy import TestSequenceStrategy as helper


class TestBiggestGapBisectionSequence(unittest.TestCase):

    def test_sbg_sequence_always_available(self):
        state_factory = helper.create_state_factory(helper.always_has_binary)
        sequence = BiggestGapBisectionSequence(state_factory, 12)
        index_sequence = [sequence.next().index for _ in range(12)]
        assert index_sequence == [0, 99, 49, 74, 24, 36, 61, 86, 12, 42, 67, 92]
        self.assertRaises(SequenceFinished, sequence.next)

    def test_sbg_sequence_even_available(self):
        state_factory = helper.create_state_factory(helper.only_has_binaries_for_even)
        sequence = BiggestGapBisectionSequence(state_factory, 12)
        index_sequence = [sequence.next().index for _ in range(12)]
        assert index_sequence == [0, 98, 50, 26, 74, 14, 38, 62, 86, 8, 20, 32]

    def test_sbg_sequence_almost_none_available(self):
        state_factory = helper.create_state_factory(helper.has_very_few_binaries)
        sequence = BiggestGapBisectionSequence(state_factory, 10)
        index_sequence = [sequence.next().index for _ in range(10)]
        assert index_sequence == [0, 99, 44, 66, 22, 77, 11, 33, 55, 88]
        self.assertRaises(SequenceFinished, sequence.next)

    def test_sbg_sequence_sparse_first_half_avaiable(self):
        state_factory = helper.create_state_factory(helper.has_very_few_binaries_in_first_half)
        sequence = BiggestGapBisectionSequence(state_factory, 17)
        index_sequence = [sequence.next().index for _ in range(17)]
        assert index_sequence == [0, 99, 50, 22, 74, 44, 86, 62, 92, 56, 68, 80, 95, 53, 59, 65, 71]

    def test_sbg_sequence_always_available_with_evaluated_states(self):
        state_factory = helper.create_state_factory(helper.always_has_binary, evaluated_indexes=[49, 61])
        sequence = BiggestGapBisectionSequence(state_factory, 17)
        index_sequence = [sequence.next().index for _ in range(15)]
        print(index_sequence)
        assert index_sequence == [0, 99, 24, 80, 36, 12, 70, 89, 42, 6, 18, 30, 55, 75, 94]
        self.assertRaises(SequenceFinished, sequence.next)
