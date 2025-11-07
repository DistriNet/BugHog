from __future__ import annotations

import logging
from typing import Optional

from bughog.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bughog.search_strategy.sequence_strategy import SequenceFinished
from bughog.version_control.state.base import State
from bughog.version_control.state_factory import StateFactory

logger = logging.getLogger(__name__)


class BiggestGapBisectionSearch(BiggestGapBisectionSequence):
    """
    This search strategy will split the biggest gap between two states in half and return the state in the middle.
    It will only consider state pairs if their non-dirty result differs.
    It stops when there are no more states to evaluate between two states with different outcomes.
    """

    def __init__(self, state_factory: StateFactory, considered_states: Optional[list[State]] = None) -> None:
        """
        Initializes the search strategy.

        :param state_factory: The factory to create new states.
        :param considered_states: States that have already been returned.
        """
        super().__init__(state_factory, 0, considered_states=considered_states)

    def next(self, wait=True) -> State:
        """
        Returns the next state to evaluate.
        """
        # Fetch all evaluated states
        self._fetch_evaluated_states(wait=wait)

        if self._limit and self._limit <= len(self._considered_states):
            raise SequenceFinished()

        if self._lower_state not in self._considered_states:
            self._add_state(self._lower_state)
            return self._lower_state
        if self._upper_state not in self._considered_states:
            self._add_state(self._upper_state)
            return self._upper_state

        while next_pair := self.__get_next_pair_to_split():
            splitter_state = self._find_best_splitter_state(next_pair[0], next_pair[1])
            if splitter_state is None:
                # No available splitter state was found.
                self._unavailability_gap_pairs.add(next_pair)
            else:
                # The state is not considered yet.
                logger.debug(f'Splitting [{next_pair[0].index}]--/{splitter_state.index}/--[{next_pair[1].index}]')
                self._add_state(splitter_state)
                return splitter_state

        raise SequenceFinished()

    def __get_next_pair_to_split(self, pinpoint_error_shifts=False) -> Optional[tuple[State, State]]:
        """
        Returns the next pair to split.
        """
        states = self._considered_states

        # There should be at least one state in between the outer states, otherwise we cannot split.
        if not states[0].index + 1 < states[-1].index:
            return None

        # For each clean state, we find the closest next clean state, and make pairs in between them.
        pairs = []
        for i in range(0, len(states)):
            if not states[i].has_result() or states[i].has_dirty_result():
                continue
            j = self.__find_next_clean_state(states, i)
            if j is None:
                break
            elif states[i].has_same_outcome(states[j]):
                pass
            else:
                new_pairs = self.__create_pairs_between_clean_states(states[i:j+1])
                pairs.extend(new_pairs)

        # Remove pairs that cannot be split.
        pairs = [pair for pair in pairs if pair[0].index + 1 < pair[1].index]
        if len(pairs) == 0:
            return None

        # Remove pairs already identified as unavailability gaps.
        pairs = [pair for pair in pairs if pair not in self._unavailability_gap_pairs]
        if len(pairs) == 0:
            return None

        # Sort pairs from largest to smallest range.
        pairs.sort(key=lambda pair: pair[1].index - pair[0].index, reverse=True)
        return pairs[0]

    @staticmethod
    def __find_next_clean_state(states: list[State], start: int) -> int | None:
        """
        Returns the index of the next state with a clean result, with the search starting after the given start index.
        """
        for i in range(start + 1, len(states)):
            if states[i].has_result() and not states[i].has_dirty_result():
                return i
        return None

    @staticmethod
    def __create_pairs_between_clean_states(states: list[State]) -> list[tuple[State,State]]:
        """
        Creates pairs of a sequence bordered by two clean states.
        We assume there are no other clean states in this range.
        """
        return[
            pair for pair in zip(states, states[1:])
            if not (pair[0].has_dirty_result() and pair[1].has_dirty_result())
        ]

    @staticmethod
    def create_from_bgb_sequence(bgb_sequence: BiggestGapBisectionSequence) -> BiggestGapBisectionSearch:
        """
        Returns a BGB search object, which continues on state of the given BGB sequence object.

        :param bgb_sequence: The BGB sequence object from which the state will be used to create the BGB search object.
        """
        return BiggestGapBisectionSearch(bgb_sequence._state_factory, considered_states=bgb_sequence._considered_states)
