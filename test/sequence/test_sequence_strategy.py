import unittest
from unittest.mock import patch
from bci.search_strategy.n_ary_sequence import NArySequence, SequenceFinished


class TestSequenceStrategy(unittest.TestCase):

    @staticmethod
    def always_true(_):
        return True

    @staticmethod
    def only_even(x):
        return x % 2 == 0

    def test_binary_sequence(self):
        values = list(range(100))
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            seq = NArySequence(values, 2)
            assert seq.next() == 0
            assert seq.next() == 99
            assert seq.next() == 50

    def test_binary_sequence_ending(self):
        values = list(range(10))
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            seq = NArySequence(values, 2)
            assert seq.next() == 0
            assert seq.next() == 9
            assert seq.next() == 5
            assert seq.next() == 3
            assert seq.next() == 8
            assert seq.next() == 2
            assert seq.next() == 4
            assert seq.next() == 7
            assert seq.next() == 1
            assert seq.next() == 6
            self.assertRaises(SequenceFinished, seq.next)

    def test_binary_sequence_ending_only_even_available(self):
        values = list(range(100))
        with patch('bci.browser.binary.factory.binary_is_available', self.only_even):
            seq = NArySequence(values, 2)
            outputted_values = set()
            for _ in range(50):
                n = seq.next()
                assert n % 2 == 0
                assert n not in outputted_values
                outputted_values.add(n)
            self.assertRaises(SequenceFinished, seq.next)

    def test_3ary_sequence(self):
        values = list(range(100))
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            seq = NArySequence(values, 3)
            assert seq.next() == 0
            assert seq.next() == 99
            assert seq.next() == 34
            assert seq.next() == 67
            assert seq.next() == 12
            assert seq.next() == 23
            assert seq.next() == 46
            assert seq.next() == 57
            assert seq.next() == 79
            assert seq.next() == 90

    def test_3nary_sequence_ending(self):
        values = list(range(10))
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            seq = NArySequence(values, 3)
            assert seq.next() == 0
            assert seq.next() == 9
            assert seq.next() == 4
            assert seq.next() == 7
            assert seq.next() == 2
            assert seq.next() == 3
            assert seq.next() == 5
            assert seq.next() == 6
            assert seq.next() == 8
            assert seq.next() == 1
            self.assertRaises(SequenceFinished, seq.next)

    def test_3nary_sequence_ending_only_even_available(self):
        values = list(range(100))
        with patch('bci.browser.binary.factory.binary_is_available', self.only_even):
            seq = NArySequence(values, 3)
            outputted_values = set()
            for _ in range(50):
                n = seq.next()
                assert n % 2 == 0
                assert n not in outputted_values
                outputted_values.add(n)
            self.assertRaises(SequenceFinished, seq.next)

    def test_4ary_sequence(self):
        values = list(range(100))
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            seq = NArySequence(values, 4)
            assert seq.next() == 0
            assert seq.next() == 99
            assert seq.next() == 26
            assert seq.next() == 51
            assert seq.next() == 76

    def test_4nary_sequence_ending(self):
        values = list(range(10))
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            seq = NArySequence(values, 4)
            assert seq.next() == 0
            assert seq.next() == 9
            assert seq.next() == 3
            assert seq.next() == 5
            assert seq.next() == 7
            assert seq.next() == 1
            assert seq.next() == 2
            assert seq.next() == 4
            assert seq.next() == 6
            assert seq.next() == 8
            self.assertRaises(SequenceFinished, seq.next)

    def test_4nary_sequence_ending_only_even_available(self):
        values = list(range(100))
        with patch('bci.browser.binary.factory.binary_is_available', self.only_even):
            seq = NArySequence(values, 4)
            outputted_values = set()
            for _ in range(50):
                n = seq.next()
                assert n % 2 == 0
                assert n not in outputted_values
                outputted_values.add(n)
            self.assertRaises(SequenceFinished, seq.next)

    def test_limit(self):
        values = list(range(100))
        with patch('bci.browser.binary.factory.binary_is_available', self.always_true):
            seq = NArySequence(values, 2, limit=37)
            for _ in range(37):
                seq.next()
            self.assertRaises(SequenceFinished, seq.next)
