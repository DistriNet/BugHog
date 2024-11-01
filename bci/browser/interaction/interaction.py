import logging
from inspect import signature

from bci.browser.configuration.browser import Browser as BrowserConfig
from bci.browser.interaction.simulation import Simulation
from bci.evaluations.logic import TestParameters

logger = logging.getLogger(__name__)


class Interaction:
    browser: BrowserConfig
    script: list[str]
    params: TestParameters

    def __init__(self, browser: BrowserConfig, script: list[str], params: TestParameters) -> None:
        self.browser = browser
        self.script = script
        self.params = params

    def execute(self) -> None:
        simulation = Simulation(self.browser, self.params)

        if self._interpret(simulation):
            simulation.sleep(str(self.browser.get_navigation_sleep_duration()))
            simulation.navigate('https://a.test/report/?bughog_sanity_check=OK')

    def _interpret(self, simulation: Simulation) -> bool:
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

            try:
                method(*args)
            except:
                return False

        return True
