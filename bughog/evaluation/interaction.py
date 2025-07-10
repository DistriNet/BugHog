import logging
from inspect import signature
from urllib.parse import quote_plus

from bughog.parameters import EvaluationParameters
from bughog.subject.simulation import Simulation
from bughog.subject.webbrowser.interaction.simulation import SimulationException

logger = logging.getLogger(__name__)


class Interaction:

    def __init__(self, script: list[str], params: EvaluationParameters) -> None:
        self.script = script
        self.params = params

    def execute(self, simulation: Simulation) -> None:
        if self._interpret(simulation):
            simulation.sleep(str(simulation.executable.navigation_sleep_duration))
            simulation.do_sanity_check()

    def _interpret(self, simulation: Simulation) -> bool:
        try:
            for statement in self.script:
                if statement.strip() == '' or statement[0] == '#':
                    continue

                cmd, *args = statement.split()
                method_name = cmd.lower()

                if method_name not in simulation.supported_commands:
                    raise Exception(
                        f'Invalid command `{cmd}`. Expected one of {", ".join(map(lambda m: m.upper(), simulation.supported_commands))}.'
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
