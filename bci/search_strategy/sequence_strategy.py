import logging
from abc import abstractmethod
from threading import Thread
from typing import Optional

from bci.version_control.factory import StateFactory
from bci.version_control.states.state import State

logger = logging.getLogger(__name__)


class SequenceStrategy:
    def __init__(self, state_factory: StateFactory, limit) -> None:
        """
        Initializes the sequence strategy.

        :param state_factory: The factory to create new states.
        :param limit: The maximum number of states to evaluate. 0 means no limit.
        """
        self._state_factory = state_factory
        self._limit = limit
        self._lower_state, self._upper_state = self.__create_available_boundary_states()
        self._completed_states = []

    @abstractmethod
    def next(self) -> State:
        pass

    def is_available(self, state: State) -> bool:
        return state.has_available_binary()

    def _add_state(self, elem: State) -> None:
        """
        Adds an element to the list of evaluated states and sorts the list.
        """
        self._completed_states.append(elem)
        self._completed_states.sort(key=lambda x: x.index)

    def _fetch_evaluated_states(self) -> None:
        """
        Fetches all evaluated states from the database and stores them in the list of evaluated states.
        """
        fetched_states = self._state_factory.create_evaluated_states()
        for state in self._completed_states:
            if state not in fetched_states:
                fetched_states.append(state)
        fetched_states.sort(key=lambda x: x.index)
        self._completed_states = fetched_states

    def __create_available_boundary_states(self) -> tuple[State, State]:
        first_state, last_state = self._state_factory.boundary_states
        available_first_state = self._find_closest_state_with_available_binary(first_state, (first_state, last_state))
        available_last_state = self._find_closest_state_with_available_binary(last_state, (first_state, last_state))
        if available_first_state is None or available_last_state is None:
            raise AttributeError(
                f"Could not find boundary states for '{self._lower_state.index}' and '{self._upper_state.index}'"
            )
        return available_first_state, available_last_state

    def _find_closest_state_with_available_binary(self, target: State, boundaries: tuple[State, State]) -> State | None:
        """
        Finds the closest state with an available binary **strictly** within the given boundaries.
        """
        if target.has_available_binary():
            return target

        def index_has_available_binary(index: int) -> Optional[State]:
            state = self._state_factory.create_state(index)
            if state.has_available_binary():
                return state
            else:
                return None

        diff = 1
        first_state, last_state = boundaries
        best_splitter_index = target.index
        while (best_splitter_index - diff - 1) > first_state.index or (best_splitter_index + diff + 1) < last_state.index:
            threads = []
            for offset in (-diff, diff, - 1 - diff, 1 + diff):
                target_index = best_splitter_index + offset
                if first_state.index < target_index < last_state.index:
                    thread = ThreadWithReturnValue(target=index_has_available_binary, args=(target_index,))
                    thread.start()
                    threads.append(thread)

            for thread in threads:
                state = thread.join()
                if state:
                    return state
            diff += 2
        return None


class SequenceFinished(Exception):
    pass


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return
