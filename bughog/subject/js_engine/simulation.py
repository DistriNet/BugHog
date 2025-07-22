from bughog.subject.simulation import Simulation


class JSEngineSimulation(Simulation):
    @property
    def supported_commands(self) -> list[str]:
        return ['run']

    def do_sanity_check(self):
        # A sanity check is supposed to be performed within the proof of concept.
        pass
        # self.executable.run(['-e', "print('bughog_sanity_check=ok')"], timeout=1)

    def report_simulation_error(self, message: str):
        # TODO: report simulation errors
        pass

    # Script commands

    def run(self, file_name: str):
        self.executable.run([file_name], cwd=self.context)
        self.executable.terminate(wait=True)
