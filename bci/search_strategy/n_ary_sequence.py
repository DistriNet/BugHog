import math
from queue import Queue
from bci.search_strategy.sequence_elem import ElemState, SequenceElem
from bci.search_strategy.sequence_strategy import SequenceStrategy, SequenceFinished
from bci.version_control.states.state import State


class NArySequence(SequenceStrategy):

    def __init__(self, values: list[State], n: int, limit=float('inf'), prior_elems: list[SequenceElem] = None) -> None:
        super().__init__(values, prior_elems=prior_elems)
        self.n = n
        first_index = 0
        last_index = len(self._elems) - 1
        self.index_queue = Queue()
        self.index_queue.put(first_index)
        self.index_queue.put(last_index)
        self.range_queue = Queue()
        self.range_queue.put((first_index + 1, last_index))
        self.limit = limit
        self.nb_of_started_evaluations = 0

    def next(self) -> State:
        while True:
            if self.limit <= self.nb_of_started_evaluations:
                raise SequenceFinished()
            while self.index_queue.empty():
                if self.range_queue.empty():
                    raise SequenceFinished()
                (lower_index, higher_index) = self.range_queue.get()
                new_indexes, new_ranges = self.divide_range(lower_index, higher_index, self.n)
                for new_index in new_indexes:
                    self.index_queue.put(new_index)
                for new_range in new_ranges:
                    self.range_queue.put(new_range)
            target_elem = self.index_queue.get()
            closest_available_elem = self.find_closest_available_elem(target_elem)
            self.logger.debug(f"Next state should be {repr(target_elem)}, but {repr(closest_available_elem)} is closest available")
            if closest_available_elem.state == ElemState.INITIALIZED:
                closest_available_elem.state = ElemState.IN_PROGRESS
                self.nb_of_started_evaluations += 1
                return closest_available_elem.value

    @staticmethod
    def divide_range(lower_index, higher_index, n):
        if lower_index == higher_index:
            return [], []
        if higher_index - lower_index + 1 <= n:
            return list(range(lower_index, higher_index)), []
        step = math.ceil((higher_index - lower_index) / n)
        if lower_index + step * n <= higher_index:
            indexes = list(range(lower_index, higher_index + 1, step))
        else:
            indexes = list(range(lower_index, higher_index + 1, step)) + [higher_index]
        ranges = []
        ranges.append((indexes[0], indexes[1]))
        for i in range(1, len(indexes) - 1):
            ranges.append((indexes[i] + 1, indexes[i + 1]))
        return indexes[1:-1], ranges
