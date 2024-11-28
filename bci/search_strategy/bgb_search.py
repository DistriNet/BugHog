from __future__ import annotations

import logging
from typing import Optional

from bci.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bci.search_strategy.sequence_strategy import SequenceFinished
from bci.version_control.factory import StateFactory
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)


class BiggestGapBisectionSearch(BiggestGapBisectionSequence):
    """
    This search strategy will split the biggest gap between two states in half and return the state in the middle.
    It will only consider states where the non-None outcome differs.
    It stops when there are no more states to evaluate between two states with different outcomes.
    """

    def __init__(self, state_factory: StateFactory, completed_states: Optional[list[State]]=None) -> None:
        """
        Initializes the search strategy.

        :param state_factory: The factory to create new states.
        :param completed_states: States that have already been returned.
        """
        super().__init__(state_factory, 0, completed_states=completed_states)

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

        while next_pair := self.__get_next_pair_to_split():
            splitter_state = self._find_best_splitter_state(next_pair[0], next_pair[1])
            if splitter_state is None:
                self._unavailability_gap_pairs.add(next_pair)
            if splitter_state:
                logger.debug(f'Splitting [{next_pair[0].index}]--/{splitter_state.index}/--[{next_pair[1].index}]')
                self._add_state(splitter_state)
                return splitter_state
        raise SequenceFinished()

    def __get_next_pair_to_split(self) -> Optional[tuple[State, State]]:
        """
        Returns the next pair of states to split.
        """
        # Make pairwise list of states and remove pairs with the same outcome
        states = self._completed_states
        pairs = [(state1, state2) for state1, state2 in zip(states, states[1:]) if state1.outcome != state2.outcome]
        if not pairs:
            return None
        # Remove the first and last pair if they have a first and last state with a None outcome, respectively
        if pairs[0][0].outcome is None:
            pairs = pairs[1:]
        if pairs[-1][1].outcome is None:
            pairs = pairs[:-1]
        # Remove all pairs that have already been identified as unavailability gaps
        pairs = [pair for pair in pairs if pair not in self._unavailability_gap_pairs]
        # Remove any pair where the same None-outcome state is present in a pair where the sibling states have the same outcome
        pairs_with_failed = [pair for pair in pairs if pair[0].outcome is None or pair[1].outcome is None]
        for i in range(0, len(pairs_with_failed), 2):
            if i + 1 >= len(pairs_with_failed):
                break
            first_pair = pairs_with_failed[i]
            second_pair = pairs_with_failed[i + 1]
            if first_pair[0].outcome == second_pair[1].outcome:
                pairs.remove(first_pair)
                pairs.remove(second_pair)

        if not pairs:
            return None
        # Sort pairs to prioritize pairs with bigger gaps.
        # This way, we refrain from pinpointing pair-by-pair, making the search more efficient.
        # E.g., when the splitter of the first gap is being evaluated, we can already evaluate the
        # splitter of the second gap with having to wait for the first gap to be fully evaluated.
        pairs.sort(key=lambda pair: pair[1].index - pair[0].index, reverse=True)
        return pairs[0]

    @staticmethod
    def create_from_bgb_sequence(bgb_sequence: BiggestGapBisectionSequence) -> BiggestGapBisectionSearch:
        """
        Returns a BGB search object, which continues on state of the given BGB sequence object.

        :param bgb_sequence: The BGB sequence object from which the state will be used to create the BGB search object.
        """
        return BiggestGapBisectionSearch(bgb_sequence._state_factory, completed_states=bgb_sequence._completed_states)
