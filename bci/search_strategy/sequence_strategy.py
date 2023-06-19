import logging
from abc import abstractmethod
from threading import Thread
import bci.browser.binary.factory as binary_factory
from bci.search_strategy.sequence_elem import SequenceElem
from bci.version_control.states.state import State


class SequenceStrategy:
    def __init__(self, values: list[State], prior_elems: list[SequenceElem] = None) -> None:
        self.logger = logging.getLogger("bci")
        if prior_elems and len(values) != len(prior_elems):
            raise AttributeError(f"List of values and list of elems should be of equal length ({len(values)} != {len(prior_elems)})")
        self.values = values
        if prior_elems:
            self._elems = prior_elems
        else:
            self._elems = [SequenceElem(index, value) for index, value in enumerate(values)]
        self._elem_info = {
            elem.value: elem
            for elem in self._elems
        }

    def update_outcome(self, elem: State, outcome: bool) -> None:
        self._elem_info[elem].update_outcome(outcome)

    def is_available(self, state: State) -> bool:
        return binary_factory.binary_is_available(state)

    @abstractmethod
    def next(self) -> State:
        pass

    def find_closest_available_elem(self, target_index: int) -> SequenceElem:
        diff = 0
        while True:
            potential_indexes = set(index for index in [
                target_index + diff,
                target_index + diff + 1,
                target_index - diff,
                target_index - diff - 1,
            ] if 0 <= index < len(self._elems))

            if not potential_indexes:
                raise AttributeError(f"Could not find closest available build state for '{target_index}'")
            threads = []
            for index in potential_indexes:
                thread = ThreadWithReturnValue(target=lambda x: x if self._elems[x].is_available() else None, args=(index,))
                thread.start()
                threads.append(thread)

            results = []
            for thread in threads:
                result = thread.join()
                if result is not None:
                    results.append(result)
            # If valid results are found, return the one closest to target
            if results:
                results = sorted(results, key=lambda x: abs(x - target_index))
                return self._elems[results[0]]
            # Otherwise re-iterate
            diff += 2


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
