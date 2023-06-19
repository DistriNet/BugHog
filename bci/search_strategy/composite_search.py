from bci.search_strategy.sequence_strategy import SequenceStrategy
from bci.search_strategy.n_ary_sequence import NArySequence, SequenceFinished
from bci.search_strategy.n_ary_search import NArySearch
from bci.search_strategy.sequence_elem import SequenceElem, ElemState
from bci.version_control.states.state import State


class CompositeSearch(SequenceStrategy):
    def __init__(
                self,
                values: list[State],
                n: int,
                sequence_limit: int,
                sequence_strategy_class: NArySequence.__class__,
                search_strategy_class: NArySearch.__class__) -> None:
        super().__init__(values)
        self.n = n
        self.sequence_strategy = sequence_strategy_class(values, n, limit=sequence_limit)
        self.search_strategies = []
        self.search_strategy_class = search_strategy_class
        self.sequence_strategy_finished = False

    def next(self) -> State:
        if not self.sequence_strategy_finished:
            next_elem = self.next_in_sequence_strategy()
            if next_elem is not None:
                return next_elem
        return self.next_in_search_strategy()

    def next_in_sequence_strategy(self) -> State:
        try:
            return self.sequence_strategy.next()
        except SequenceFinished:
            self.sequence_strategy_finished = True
            self.prepare_search_strategies()
            return None

    def next_in_search_strategy(self) -> State:
        while True:
            if not self.search_strategies:
                raise SequenceFinished()
            search_strategy = self.search_strategies[0]
            try:
                return search_strategy.next()
            except SequenceFinished:
                del self.search_strategies[0]

    def get_active_strategy(self) -> SequenceStrategy:
        if not self.sequence_strategy_finished:
            return self.sequence_strategy
        elif self.search_strategies:
            return self.search_strategies[0]
        else:
            raise AttributeError("No strategy is currently active")

    def update_outcome(self, elem: State, outcome: bool) -> None:
        self.get_active_strategy().update_outcome(elem, outcome)
        # We only update the outcome of this object too if we are still using the sequence strategy
        # because the elem lists need to be synced up until the search strategies are prepared.
        # Not very clean, but does the job for now.
        if not self.sequence_strategy_finished:
            super().update_outcome(elem, outcome)

    def prepare_search_strategies(self):
        shift_index_pairs = self.find_all_shift_index_pairs()
        self.search_strategies = [self.search_strategy_class(
                self.sequence_strategy.values[left_shift_index:right_shift_index+1],
                self.n,
                prior_elems=self.get_elems_slice(left_shift_index, right_shift_index+1))
            for left_shift_index, right_shift_index in shift_index_pairs]

    def get_elems_slice(self, start: int, end: int) -> list[SequenceElem]:
        return [elem.get_deep_copy(index=i) for i, elem in enumerate(self._elems[start:end])]

    def find_all_shift_index_pairs(self) -> list[tuple[int, int]]:
        # Filter out all errors and unevaluated elements
        filtered_elems = [elem for elem in self._elems if elem.state not in [ElemState.ERROR, ElemState.INITIALIZED]]
        filtered_elems_outcomes = [elem.outcome for elem in filtered_elems]
        # Get start indexes of shift in outcome
        shift_indexes = [i for i in range(0, len(filtered_elems_outcomes) - 1) if filtered_elems_outcomes[i] != filtered_elems_outcomes[i+1]]
        # Convert to index pairs for original value list
        shift_elem_pairs = [(filtered_elems[shift_index], filtered_elems[shift_index + 1]) for shift_index in shift_indexes if shift_index + 1 < len(filtered_elems)]
        shift_index_pairs = [(left_shift_elem.index, right_shift_elem.index) for left_shift_elem, right_shift_elem in shift_elem_pairs]
        return shift_index_pairs
