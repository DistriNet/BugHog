import logging
from inspect import signature
from urllib.parse import quote_plus

from bughog.subject.interaction import Interaction
from bughog.subject.webbrowser.executable import BrowserExecutable
from bughog.subject.webbrowser.interaction.simulation import Simulation
from bughog.subject.webbrowser.interaction.simulation_exception import SimulationException

logger = logging.getLogger(__name__)


class BrowserInteraction(Interaction):

    def __init__(self, executable: BrowserExecutable, script: list[str], params: ExperimentParameters) -> None:
        super().__init__(executable, script, params)

    def _do_experiment(self) -> None:
        simulation = Simulation(self.executable, self.params)
        if self._interpret(simulation):
            simulation.sleep(str(self.executable.get_navigation_sleep_duration()))

    def _do_sanity_check(self) -> None:
        simulation = Simulation(self.executable, self.params)
        if self._interpret(simulation):
            simulation.navigate('https://a.test/report/?bughog_sanity_check=OK')


    def _interpret(self, simulation: Simulation) -> bool:
        try:
            for statement in self.script:
                if statement.strip() == '' or statement[0] == '#':
                    continue

                cmd, *args = statement.split()
                method_name = cmd.lower()

                if method_name not in Simulation.public_methods:
                    raise Exception(
                        f'Invalid command `{cmd}`. Expected one of {", ".join(map(lambda m: m.upper(), Simulation.public_methods))}.'
                    )

                method = getattr(simulation, method_name)
                method_params = list(signature(method).parameters.values())

                # Allow different number of arguments only for variable argument number (*)
                if len(method_params) != len(args) and (len(method_params) < 1 or str(method_params[0])[0] != '*'):
                    raise Exception(
                        f'Invalid number of arguments for command `{cmd}`. Expected {len(method_params)}, got {len(args)}.'
                    )

                logger.debug(f'Executing interaction method `{method_name}` with the arguments {args}')

                method(*args)

            return True
        except SimulationException as e:
            # Simulation exception - sane behaviour, but do not continue interpreting
            simulation.navigate(f'https://a.test/report/?exception={quote_plus(str(e))}')
            return True
        except Exception as e:
            # Unexpected exception type - not sane, report the exception
            simulation.navigate(
                f'https://a.test/report/?uncaught-exception={quote_plus(type(e).__name__)}&message={quote_plus(str(e))}'
            )
            return False
