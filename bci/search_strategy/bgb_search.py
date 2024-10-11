import logging

from bci.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bci.search_strategy.sequence_strategy import SequenceFinished
from bci.version_control.factory import StateFactory
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)


class BiggestGapBisectionSearch(BiggestGapBisectionSequence):
    """
    This search strategy will split the biggest gap between two states in half and return the state in the middle.
    It will prioritize gaps with different outcomes and bigger gaps.
    It stops when there are no more states to evaluate between two states with different outcomes.
    """
    def __init__(self, state_factory: StateFactory) -> None:
        """
        Initializes the search strategy.

        :param state_factory: The factory to create new states.
        """
        super().__init__(state_factory, 0)

    def next(self) -> State:
        """
        Returns the next state to evaluate.
        """
        # Fetch all evaluated states
        self._fetch_evaluated_states()

        if self._limit and self._limit <= len(self._completed_states):
            raise SequenceFinished()

        if self._lower_state not in self._completed_states:
            self._add_state(self._lower_state)
            return self._lower_state
        if self._upper_state not in self._completed_states:
            self._add_state(self._upper_state)
            return self._upper_state

        # Select a pair to bisect
        pairs = list(zip(self._completed_states, self._completed_states[1:]))
        # Filter out all gap pairs (pairs defining ranges without any available binaries)
        pairs = [pair for pair in pairs if pair not in self._unavailability_gap_pairs]
        while self.__continue_search():
            # Prioritize pairs according to the max_key function
            next_pair = max(pairs, key=self.max_key)
            splitter_state = self._find_best_splitter_state(next_pair[0], next_pair[1])
            if splitter_state is None:
                self._unavailability_gap_pairs.add(next_pair)
            if splitter_state:
                logger.debug(
                    f"Splitting [{next_pair[0].index}]--/{splitter_state.index}/--[{next_pair[1].index}]"
                )
                self._add_state(splitter_state)
                return splitter_state
            pairs.remove(next_pair)
        raise SequenceFinished()

    @staticmethod
    def max_key(pair: tuple[State, State]) -> tuple[bool, int]:
        """
        Returns a score used for deciding the order of pairs.
        Pairs are sorted in the following way:
        1. Pairs with different non-None outcomes are considered first.
        2. After that, pairs with the biggest gap are considered first.
        """
        return (
            pair[0].outcome is not None and pair[1].outcome is not None and pair[0].outcome != pair[1].outcome,
            pair[1].index - pair[0].index,
        )

    def __continue_search(self) -> bool:
        """
        Returns True if the search should continue.
        This is the case if there are still unevaluated states between two states with different non-None outcomes.
        """
        # Filter out all states with a None outcome
        states = [state for state in self._completed_states if state.outcome is not None]
        # Make pairs with different outcomes
        pairs = [(state1, state2) for state1, state2 in zip(states, states[1:]) if state1.outcome != state2.outcome]
        for first, last in pairs:
            # Check if all states between first and last are either evaluated or unavailable
            for index in [index for index in range(first.index + 1, last.index)]:
                state = self._state_factory.create_state(index)
                if state not in self._completed_states and not self._state_is_in_unavailability_gap(state):
                    return True
        return False
