import logging
from typing import Optional

from bughog.search_strategy.sequence_strategy import SequenceFinished, SequenceStrategy
from bughog.version_control.state.base import State
from bughog.version_control.state_factory import StateFactory

logger = logging.getLogger(__name__)


class BiggestGapBisectionSequence(SequenceStrategy):
    """
    This sequence strategy will split the biggest gap between two states in half and return the state in the middle.
    """

    def __init__(self, state_factory: StateFactory, limit: int, considered_states: Optional[list[State]] = None) -> None:
        """
        Initializes the sequence strategy.

        :param state_factory: The factory to create new states.
        :param limit: The maximum number of states to evaluate. 0 means no limit.
        :param considered_states: States that have already been returned.
        """
        super().__init__(state_factory, limit, considered_states=considered_states)
        self._unavailability_gap_pairs: set[tuple[State, State]] = set()
        """Tuples in this list are **strict** boundaries of ranges without any available binaries."""

    def next(self) -> State:
        """
        Returns the next state to evaluate.
        """
        # Fetch all evaluated states on the first call
        if not self._considered_states:
            self._fetch_evaluated_states()

        if self._limit and self._limit <= len(self._considered_states):
            raise SequenceFinished()

        if self._lower_state not in self._considered_states:
            self._add_state(self._lower_state)
            return self._lower_state
        if self._upper_state not in self._considered_states:
            self._add_state(self._upper_state)
            return self._upper_state

        pairs = list(zip(self._considered_states, self._considered_states[1:]))
        while pairs:
            filtered_pairs = [pair for pair in pairs if not self._pair_is_in_unavailability_gap(pair)]
            furthest_pair = max(filtered_pairs, key=lambda x: x[1].index - x[0].index)
            splitter_state = self._find_best_splitter_state(furthest_pair[0], furthest_pair[1])
            if splitter_state is None:
                self._unavailability_gap_pairs.add(furthest_pair)
            elif splitter_state:
                logger.debug(f'Splitting [{furthest_pair[0].index}]--/{splitter_state.index}/--[{furthest_pair[1].index}]')
                self._add_state(splitter_state)
                return splitter_state
            pairs.remove(furthest_pair)
        raise SequenceFinished()

    def _find_best_splitter_state(self, first_state: State, last_state: State) -> Optional[State]:
        """
        Returns the most suitable state that splits the gap between the two states.
        The state should be as close as possible to the middle of the gap and should have an available binary.
        """
        if first_state.index + 1 == last_state.index:
            return None
        best_splitter_index = first_state.index + (last_state.index - first_state.index) // 2
        target_state = self._state_factory.create_state(best_splitter_index)
        return self._find_closest_state_with_available_binary(target_state, (first_state, last_state))

    def _state_is_in_unavailability_gap(self, state: State) -> bool:
        """
        Returns True if the state is in a gap between two states without any available binaries.
        """
        for pair in self._unavailability_gap_pairs:
            if pair[0].index < state.index < pair[1].index:
                return True
        return False

    def _pair_is_in_unavailability_gap(self, pair: tuple[State, State]) -> bool:
        """
        Returns True if the pair of states is in a gap between two states without any available binaries
        """
        for gap_pair in self._unavailability_gap_pairs:
            if gap_pair[0].index < pair[0].index < gap_pair[1].index and gap_pair[0].index < pair[1].index < gap_pair[1].index:
                return True
        return False
