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

        # Search
        print(sequence.next().index)
        # assert sequence.next().index == 55
        # self.assertRaises(SequenceFinished, sequence.next)
