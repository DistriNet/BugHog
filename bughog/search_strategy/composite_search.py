from typing import Optional
from bughog.search_strategy.bgb_search import BiggestGapBisectionSearch
from bughog.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bughog.search_strategy.sequence_strategy import SequenceFinished
from bughog.version_control.state_factory import StateFactory
from bughog.version_control.state.base import State


class CompositeSearch():
    def __init__(self, state_factory: StateFactory, sequence_limit: int) -> None:
        self.sequence_strategy = BiggestGapBisectionSequence(state_factory, limit=sequence_limit)
        self.search_strategy: Optional[BiggestGapBisectionSearch] = None

    def next(self) -> State:
        """
        Returns the next state, based on a sequence strategy and search strategy.
        First, the sequence strategy decides which state to return until it returns the SequenceFinished exception.
        From then on, the search strategy decides which state to return.
        """
        if self.search_strategy is None:
            try:
                return self.sequence_strategy.next()
            except SequenceFinished:
                self.search_strategy = BiggestGapBisectionSearch.create_from_bgb_sequence(self.sequence_strategy)
                return self.search_strategy.next()
        else:
            return self.search_strategy.next()
