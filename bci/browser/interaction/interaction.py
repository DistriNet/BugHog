import logging
import re
from inspect import signature

from bci.browser.configuration.browser import Browser as BrowserConfig
from bci.browser.interaction.browsers.browser import Browser
from bci.browser.interaction.browsers.chromium import Chromium
from bci.browser.interaction.browsers.firefox import Firefox

logger = logging.getLogger(__name__)


class Interaction:
    browser: BrowserConfig
    script: list[str]

    def __init__(self, browser: BrowserConfig, script: list[str]) -> None:
        self.browser = browser
        self.script = script

    def execute(self) -> None:
        interaction_browser = self._initiate_browser()

        self._interpret(interaction_browser)

        interaction_browser.navigate('https://a.test/report/?bughog_sanity_check=OK')

    def _initiate_browser(self) -> Browser:
        # TODO - possibly return different browser instances
        return Browser(self.browser)
        """
        cdp = re.search(
            r'DevTools listening on ws:\/\/(.+):(.+)\/devtools\/browser\/(.+)\n',
            init_output,
        )

        if cdp:
            return Chromium(browser_id=cdp.group(3), port=int(cdp.group(2)), host=cdp.group(1))

        bidi = re.search(
            r'WebDriver BiDi listening on ws:\/\/(.+):(.+)',
            init_output,
        )

        if bidi:
            return Firefox(port=int(bidi.group(2)), host=bidi.group(1))

        raise Exception('Unrecognized browser')
        """

    def _interpret(self, browser: Browser) -> None:
        for statement in self.script:
            cmd, *args = statement.split()
            method_name = cmd.lower()

            if method_name not in Browser.public_methods:
                raise Exception(
                    f'Invalid command `{cmd}`. Expected one of {", ".join(map(lambda m: m.upper(), Browser.public_methods))}.'
                )

            method = getattr(browser, method_name)
            method_params_len = len(signature(method).parameters)

            if method_params_len != len(args):
                raise Exception(
                    f'Invalid number of arguments for command `{cmd}`. Expected {method_params_len}, got {len(args)}.'
                )

            logger.debug(f'Executing interaction method `{method_name}` with the arguments {args}')
            method(*args)
