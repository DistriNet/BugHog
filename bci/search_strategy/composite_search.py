from bci.search_strategy.bgb_search import BiggestGapBisectionSearch
from bci.search_strategy.bgb_sequence import BiggestGapBisectionSequence
from bci.search_strategy.sequence_strategy import SequenceFinished
from bci.version_control.factory import StateFactory
from bci.version_control.states.state import State


class CompositeSearch():
    def __init__(self, state_factory: StateFactory, sequence_limit: int) -> None:
        self.sequence_strategy = BiggestGapBisectionSequence(state_factory, limit=sequence_limit)
        self.search_strategy = BiggestGapBisectionSearch(state_factory)
        self.sequence_strategy_finished = False

    def next(self) -> State:
        # First we use the sequence strategy to select the next state
        if not self.sequence_strategy_finished:
            try:
                return self.sequence_strategy.next()
            except SequenceFinished:
                self.sequence_strategy_finished = True
                return self.search_strategy.next()
        else:
            return self.search_strategy.next()
