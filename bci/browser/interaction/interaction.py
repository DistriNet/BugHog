import logging
from inspect import signature

from bci.browser.configuration.browser import Browser as BrowserConfig
from bci.browser.interaction.simulation import Simulation

logger = logging.getLogger(__name__)


class Interaction:
    browser: BrowserConfig
    script: list[str]

    def __init__(self, browser: BrowserConfig, script: list[str]) -> None:
        self.browser = browser
        self.script = script

    def execute(self) -> None:
        simulation = self._initiate_simulation()

        self._interpret(simulation)

        simulation.navigate('https://a.test/report/?bughog_sanity_check=OK')
        simulation.sleep('0.5')

    def _initiate_simulation(self) -> Simulation:
        # TODO - possibly return different browser instances
        return Simulation(self.browser)

    def _interpret(self, simulation: Simulation) -> None:
        for statement in self.script:
            if statement.strip() == '':
                continue

            cmd, *args = statement.split()
            method_name = cmd.lower()

            if cmd == '#':
                continue

            if method_name not in Simulation.public_methods:
                raise Exception(
                    f'Invalid command `{cmd}`. Expected one of {", ".join(map(lambda m: m.upper(), Simulation.public_methods))}.'
                )

            method = getattr(simulation, method_name)
            method_params_len = len(signature(method).parameters)

            if method_params_len != len(args):
                raise Exception(
                    f'Invalid number of arguments for command `{cmd}`. Expected {method_params_len}, got {len(args)}.'
                )

            logger.debug(f'Executing interaction method `{method_name}` with the arguments {args}')
            method(*args)
