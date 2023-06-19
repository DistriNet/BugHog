from bisect import insort

from bci.search_strategy.sequence_elem import SequenceElem
from bci.search_strategy.n_ary_sequence import NArySequence, SequenceFinished, ElemState
from bci.version_control.states.state import State


class NArySearch(NArySequence):

    def __init__(self, values: list[State], n: int, prior_elems: list[SequenceElem] = None) -> None:
        super().__init__(values, n, prior_elems=prior_elems)
        self.lower_bound = 0
        """
        Lower boundary, only indexes equal or higher should be evaluated.
        """
        self.upper_bound = len(values)
        """
        Strict upper boundary, only indexes strictly lower should be evaluated.
        """
        self.outcomes: list[tuple[int, bool]] = []
        if prior_elems:
            for elem in prior_elems:
                if elem.outcome is not None:
                    self.update_boundaries(elem.value, elem.outcome)

    def update_outcome(self, value: State, outcome: bool) -> None:
        super().update_outcome(value, outcome)
        self.update_boundaries(value, outcome)

    def update_boundaries(self, value: State, outcome: bool) -> None:
        if outcome is None:
            return
        new_index = self._elem_info[value].index
        insort(self.outcomes, (new_index, outcome), key=lambda x: x[0])
        if len(self.outcomes) < 3:
            return
        index0, outcome0 = self.outcomes[0]
        index1, outcome1 = self.outcomes[1]
        index2, outcome2 = self.outcomes[2]
        if outcome0 != outcome1:
            del self.outcomes[2]
            self.lower_bound = index0
            self.upper_bound = index1
        elif outcome1 != outcome2:
            del self.outcomes[0]
            self.lower_bound = index1
            self.upper_bound = index2
        lower_value = self._elems[self.lower_bound].value
        upper_value = self._elems[self.upper_bound - 1].value
        self.logger.info(f"Boundaries updated: {lower_value} <= x <= {upper_value}")

    def next(self) -> State:
        while True:
            while self.index_queue.empty():
                if self.range_queue.empty():
                    raise SequenceFinished()
                (lower_index, upper_index) = self.range_queue.get()
                if lower_index >= self.upper_bound or upper_index < self.lower_bound:
                    # The range is completely out of bounds, so we just discard it
                    continue
                if lower_index < self.lower_bound:
                    # The range is partly out of bounds, so we truncate it
                    # (possible because closest available elem instead of exact elem)
                    lower_index = self.lower_bound
                if upper_index > self.upper_bound:
                    # Same as above
                    upper_index = self.upper_bound
                new_indexes, new_ranges = self.divide_range(lower_index, upper_index, self.n)
                for new_index in new_indexes:
                    self.index_queue.put(new_index)
                for new_range in new_ranges:
                    self.range_queue.put(new_range)
            index = self.index_queue.get()
            # Only use index if it's within the active bounds
            # Could not be the case if the index was added to the queue after the bounds were updated
            if self.lower_bound <= index < self.upper_bound:
                # Get closest available elem and check whether it is not yet evaluated
                closest_available_elem = self.find_closest_available_elem(index)
                if closest_available_elem.state == ElemState.INITIALIZED:
                    closest_available_elem.state = ElemState.IN_PROGRESS
                    return closest_available_elem.value
