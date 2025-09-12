import logging
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from bughog.version_control.state.base import State
from bughog.version_control.state_factory import StateFactory

logger = logging.getLogger(__name__)


class SequenceStrategy:
    def __init__(self, state_factory: StateFactory, limit: int, considered_states: Optional[list[State]] = None) -> None:
        """
        Initializes the sequence strategy.

        :param state_factory: The factory to create new states.
        :param limit: The maximum number of states to evaluate. 0 means no limit.
        :param considered_states: States that have already been returned.
        """
        self._state_factory = state_factory
        self._limit = limit
        self._lower_state, self._upper_state = self.__create_available_boundary_states()
        self._considered_states = considered_states if considered_states else []

    @abstractmethod
    def next(self) -> State:
        pass

    def is_available(self, state: State) -> bool:
        return state.has_available_executable()

    def _add_state(self, elem: State) -> None:
        """
        Adds an element to the list of considered states if not already a member, and sorts the list.
        """
        if elem not in self._considered_states:
            self._considered_states.append(elem)
            self._considered_states.sort(key=lambda x: x.index)

    def _fetch_evaluated_states(self, wait=True) -> None:
        """
        Fetches all evaluated states from the database and stores them in the list of considered states.
        If wait is True, it retries until all considered states have non-None result_variables (e.i., all ongoing experiments have finished.).
        It will resume anyway after 10 retries.
        """
        fetched_states = []
        if wait:
            for _ in range(10):
                fetched_states = self._state_factory.create_evaluated_states()
                if all(state in fetched_states for state in self._considered_states):
                    break
                time.sleep(3)
        else:
            fetched_states = self._state_factory.create_evaluated_states()

        for state in self._considered_states:
            if state not in fetched_states:
                fetched_states.append(state)
        fetched_states.sort(key=lambda x: x.index)
        self._considered_states = fetched_states

    def __create_available_boundary_states(self) -> tuple[State, State]:
        first_state, last_state = self._state_factory.boundary_states
        available_first_state = self._find_closest_state_with_available_binary(first_state, (first_state, last_state))
        available_last_state = self._find_closest_state_with_available_binary(last_state, (first_state, last_state))
        if available_first_state is None or available_last_state is None:
            raise AttributeError(f"Could not find boundary states for '{self._lower_state.index}' and '{self._upper_state.index}'")
        return available_first_state, available_last_state

    def _find_closest_state_with_available_binary(self, target: State, boundaries: tuple[State, State]) -> State | None:
        """
        Finds the closest state with an available binary **strictly** within the given boundaries.
        """
        if target.has_available_executable():
            return target

        try:
            if state := self.__get_closest_available_state(target, boundaries):
                return state
            else:
                return None
        except FunctionalityNotAvailable:
            pass

        def index_has_available_executable(index: int) -> Optional[State]:
            state = self._state_factory.create_state(index)
            if state.has_available_executable():
                return state
            else:
                return None

        diff = 1
        first_state, last_state = boundaries
        best_splitter_index = target.index
        while (best_splitter_index - diff) > first_state.index or (best_splitter_index + diff) < last_state.index:
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = []
                for offset in (-diff, diff, -1 - diff, 1 + diff, -2 - diff, 2 + diff):
                    target_index = best_splitter_index + offset
                    if first_state.index < target_index < last_state.index:
                        futures.append(executor.submit(index_has_available_executable, target_index))

                for future in futures:
                    state = future.result()
                    if state:
                        return state

            diff += 2
        return None

    def __get_closest_available_state(self, target: State, boundaries: tuple[State, State]) -> State | None:
        """
        Return the closest state with an available binary.
        """
        try:
            states = target.get_previous_and_next_state_with_executable()
            states = [state for state in states if state is not None]
            ordered_states = sorted(states, key=lambda x: abs(target.commit_nb - x.commit_nb))

            for state in ordered_states:
                if boundaries[0].commit_nb < state.commit_nb < boundaries[1].commit_nb:
                    return state

            return None

        except NotImplementedError as e:
            raise FunctionalityNotAvailable() from e


class SequenceFinished(Exception):
    pass


class FunctionalityNotAvailable(Exception):
    pass
