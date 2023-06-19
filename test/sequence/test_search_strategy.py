import unittest
from unittest.mock import patch
from bci.search_strategy.n_ary_search import NArySearch
from bci.search_strategy.sequence_strategy import SequenceFinished


class TestSearchStrategy(unittest.TestCase):
    @staticmethod
    def always_true(_):
        return True

    @staticmethod
    def only_even(x):
        return x % 2 == 0

    @staticmethod
    def one_in_15(x):
        return x % 15 == 0

    def test_binary_search(self):
        def outcome(x) -> bool:
            return x < 22

        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            values = list(range(100))
            seq = NArySearch(values, 2)
            expected_elem_sequence = [0, 99, 50, 26, 14, 21, 24, 23, 22]
            elem_sequence = []
            for _ in expected_elem_sequence:
                elem = seq.next()
                seq.update_outcome(elem, outcome(elem))
                elem_sequence.append(elem)
            assert expected_elem_sequence == elem_sequence
            self.assertRaises(SequenceFinished, seq.next)

    def test_binary_search_only_even(self):
        def outcome(x) -> bool:
            return x < 22

        with patch('bci.browser.binary.factory.binary_is_available', self.only_even):
            values = list(range(100))
            seq = NArySearch(values, 2)
            expected_elem_sequence = [0, 98, 50, 26, 14, 20, 24, 22]
            elem_sequence = []
            for _ in expected_elem_sequence:
                elem = seq.next()
                seq.update_outcome(elem, outcome(elem))
                elem_sequence.append(elem)
            assert expected_elem_sequence == elem_sequence
            self.assertRaises(SequenceFinished, seq.next)

    def test_3ary_search_only_even(self):
        def outcome(x) -> bool:
            return x < 15

        with patch('bci.browser.binary.factory.binary_is_available', self.only_even):
            values = list(range(100))
            seq = NArySearch(values, 3)
            expected_elem_sequence = [0, 98, 34, 12, 24, 16, 14]
            elem_sequence = []
            for _ in expected_elem_sequence:
                elem = seq.next()
                seq.update_outcome(elem, outcome(elem))
                elem_sequence.append(elem)
            assert expected_elem_sequence == elem_sequence
            self.assertRaises(SequenceFinished, seq.next)

    def test_observer_edge_case1(self):
        def is_available(x):
            return x in [766907, 766912, 766922]

        with patch('bci.browser.binary.factory.binary_is_available', is_available):
            values = list(range(766907, 766923))
            seq = NArySearch(values, 16)
            assert seq.next() == 766907
            seq.update_outcome(766907, False)
            assert seq.next() == 766922
            seq.update_outcome(766922, True)
            assert seq.next() == 766912
            self.assertRaises(SequenceFinished, seq.next)

    def test_observer_edge_case2(self):
        def outcome(x) -> bool:
            return x < 454750

        with patch('bci.browser.binary.factory.binary_is_available', self.one_in_15):
            values = list(range(454462, 455227))
            seq = NArySearch(values, 8)
            elem_sequence = []
            while True:
                try:
                    elem = seq.next()
                    seq.update_outcome(elem, outcome(elem))
                    elem_sequence.append(elem)
                except SequenceFinished:
                    break
            assert 454740 in elem_sequence[-2:]
            assert 454725 in elem_sequence[-2:]

    def test_correct_ending_2(self):
        def outcome(x) -> bool:
            return x < 561011

        with patch('bci.browser.binary.factory.binary_is_available', self.one_in_15):
            values = list(range(560417, 562154))
            seq = NArySearch(values, 2)
            elem_sequence = []
            while True:
                try:
                    elem = seq.next()
                    seq.update_outcome(elem, outcome(elem))
                    elem_sequence.append(elem)
                except SequenceFinished:
                    break
            assert 561015 in elem_sequence[-2:]
            assert 561000 in elem_sequence[-2:]

    def test_correct_ending_4(self):
        def outcome(x) -> bool:
            return x < 561011

        with patch('bci.browser.binary.factory.binary_is_available', self.one_in_15):
            values = list(range(560417, 562154))
            seq = NArySearch(values, 4)
            elem_sequence = []
            while True:
                try:
                    elem = seq.next()
                    seq.update_outcome(elem, outcome(elem))
                    elem_sequence.append(elem)
                except SequenceFinished:
                    break
            assert 561015 in elem_sequence[-2:]
            assert 561000 in elem_sequence[-2:]

    def test_correct_ending_8(self):
        def outcome(x) -> bool:
            return x < 561011

        with patch('bci.browser.binary.factory.binary_is_available', self.one_in_15):
            values = list(range(560417, 562154))
            seq = NArySearch(values, 8)
            elem_sequence = []
            while True:
                try:
                    elem = seq.next()
                    seq.update_outcome(elem, outcome(elem))
                    elem_sequence.append(elem)
                except SequenceFinished:
                    break
            assert 561015 in elem_sequence[-2:]
            assert 561000 in elem_sequence[-2:]

    def test_correct_ending_16(self):
        def outcome(x) -> bool:
            return x < 561011

        with patch('bci.browser.binary.factory.binary_is_available', self.one_in_15):
            values = list(range(560417, 562154))
            seq = NArySearch(values, 16)
            elem_sequence = []
            while True:
                try:
                    elem = seq.next()
                    seq.update_outcome(elem, outcome(elem))
                    elem_sequence.append(elem)
                except SequenceFinished:
                    break
            assert 561015 in elem_sequence[-2:]
            assert 561000 in elem_sequence[-2:]
