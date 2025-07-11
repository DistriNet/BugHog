from bughog.subject.simulation import Simulation


class JSEngineSimulation(Simulation):

    @property
    def supported_commands(self) -> list[str]:
        return ['RUN']

    def do_sanity_check(self):
        pass
