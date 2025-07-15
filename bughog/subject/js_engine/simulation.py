from bughog.subject.simulation import Simulation


class JSEngineSimulation(Simulation):
    @property
    def supported_commands(self) -> list[str]:
        return ['run']

    def do_sanity_check(self):
        self.executable.run(['-e', "print('bughog_sanity_check=ok')"], timeout=1)

    # Script commands

    def run(self, file_name: str):
        self.executable.run([file_name], cwd=self.context, timeout=1)
