import unittest
from unittest.mock import patch
from bci.search_strategy.composite_search import CompositeSearch
from bci.search_strategy.n_ary_sequence import NArySequence
from bci.search_strategy.n_ary_search import NArySearch
from bci.search_strategy.sequence_strategy import SequenceFinished


class TestCompositeSearch(unittest.TestCase):

    @staticmethod
    def always_true(_):
        return True

    @staticmethod
    def only_even(x):
        return x % 2 == 0

    def test_find_all_shift_index_pairs(self):
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            def outcome(x) -> bool:
                return x < 22 or x > 60
            values = list(range(100))
            seq = CompositeSearch(values, 2, 10, NArySequence, NArySearch)
            seq.is_available = self.always_true
            expected_elem_sequence = [0, 99, 50, 26, 75, 14, 39, 63, 88, 8]
            elem_sequence = []
            for _ in range(10):
                elem = seq.next()
                seq.update_outcome(elem, outcome(elem))
                elem_sequence.append(elem)
            assert expected_elem_sequence == elem_sequence
            shift_index_pairs = seq.find_all_shift_index_pairs()
            assert shift_index_pairs == [(14, 26), (50, 63)]

            expected_elem_search = [21, 24, 23, 22, 57, 61, 60]
            elem_search = []
            for _ in range(len(expected_elem_search)):
                elem = seq.next()
                seq.update_outcome(elem, outcome(elem))
                elem_search.append(elem)
                assert seq.sequence_strategy_finished
            assert expected_elem_search == elem_search
            self.assertRaises(SequenceFinished, seq.next)
