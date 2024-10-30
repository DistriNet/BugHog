import re

from bci.browser.configuration.browser import Browser as BrowserConfig
from bci.browser.interaction.browsers.browser import Browser
from bci.browser.interaction.browsers.chromium import Chromium


class Interaction:
    port = 9222

    browser: BrowserConfig
    script: list[str]

    def __init__(self, browser: BrowserConfig, script: list[str]) -> None:
        self.browser = browser
        self.script = script

    def execute(self) -> None:
        output = self.browser.open()

        interaction_browser = self._initiate_browser(output)

        # TODO - parse the script and run the commands instead
        interaction_browser.navigate('https://a.test/Support/UserInteraction/main')

        interaction_browser.navigate('https://a.test/report/?bughog_sanity_check=OK')
        interaction_browser.close_connection()

        self.browser.terminate()

    def _initiate_browser(self, init_output: str) -> Browser:
        cdp = re.search(r'DevTools listening on ws:\/\/127\.0\.0\.1:9222\/devtools\/browser\/(.+)\n', init_output)

        if cdp:
            return Chromium(browser_id=cdp.group(1), port=Interaction.port)

        raise Exception('Unrecognized browser')
