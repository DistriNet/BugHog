from bci.browser.configuration.browser import Browser as BrowserConfig


class Interaction:
    browser_config: BrowserConfig
    script: list[str]

    def __init__(self, browser: BrowserConfig, script: list[str]) -> None:
        self.browser_config = browser
        self.script = script

    def execute(self) -> None:
        print(f'TODO - execute {self.browser_config._get_terminal_args()} with script {", ".join(self.script)}')
