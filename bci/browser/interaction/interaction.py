from bci.browser.automation.terminal import TerminalAutomation
from bci.browser.configuration.browser import Browser as BrowserConfig


class Interaction:
    port = 9222

    browser: BrowserConfig
    script: list[str]

    def __init__(self, browser: BrowserConfig, script: list[str]) -> None:
        self.browser = browser
        self.script = script

    def execute(self) -> None:
        output = self.browser.open()

        # TODO - identify browser from the output
        # TODO - initialize the browser
        # TODO - parse the script and run the commands
        # TODO - visit the sanity check URL
        # TODO - destroy the browser

        self.browser.terminate()
