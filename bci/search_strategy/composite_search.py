from bci.search_strategy.bgb_search import BiggestGapBisectionSearch
from bci.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bci.search_strategy.sequence_strategy import SequenceFinished, SequenceStrategy
from bci.version_control.factory import StateFactory
from bci.version_control.states.state import State, StateCondition


class CompositeSearch(SequenceStrategy):
    def __init__(self, state_factory: StateFactory, sequence_limit: int) -> None:
        super().__init__(state_factory)
        self.sequence_limit = sequence_limit
        self.sequence_strategy = BiggestGapBisectionSequence(state_factory, limit=sequence_limit)
        self.search_strategies = []
        self.sequence_strategy_finished = False

    def next(self) -> State:
        # First we use the sequence strategy to select the next state
        if not self.sequence_strategy_finished:
            try:
                return self.sequence_strategy.next()
            except SequenceFinished:
                self.sequence_strategy_finished = True
                self.prepare_search_strategies()
                return self.next_in_search_strategy()
        # If the sequence strategy is finished, we need to switch to the search strategy
        else:
            return self.next_in_search_strategy()

    def next_in_search_strategy(self) -> State:
        while True:
            if not self.search_strategies:
                raise SequenceFinished()
            search_strategy = self.search_strategies[0]
            try:
                return search_strategy.next()
            except SequenceFinished:
                del self.search_strategies[0]

    def prepare_search_strategies(self):
        self.search_strategies = []
        shift_index_pairs = self.find_all_shift_index_pairs()
        for left_shift_index, right_shift_index in shift_index_pairs:
            new_state_factory = self._state_factory.create_sibling_factory((left_shift_index, right_shift_index))
            search_strategy = BiggestGapBisectionSearch(new_state_factory)
            self.search_strategies.append(search_strategy)

    def find_all_shift_index_pairs(self) -> list[tuple[int, int]]:
        # Only consider states with a completed evaluation
        filtered_states = [state for state in self._completed_states if state.condition == [StateCondition.COMPLETED]]
        filtered_state_outcomes = [state.outcome for state in filtered_states if state.outcome]
        # Get start indexes of shift in outcome
        shift_indexes = [
            i
            for i in range(0, len(filtered_state_outcomes) - 1)
            if filtered_state_outcomes[i] != filtered_state_outcomes[i + 1]
        ]
        # Convert to index pairs for original value list
        shift_state_pairs = [
            (filtered_states[shift_index], filtered_states[shift_index + 1])
            for shift_index in shift_indexes
            if shift_index + 1 < len(filtered_states)
        ]
        shift_index_pairs = [
            (left_shift_elem.index, right_shift_state.index) for left_shift_elem, right_shift_state in shift_state_pairs
        ]
        return shift_index_pairs
