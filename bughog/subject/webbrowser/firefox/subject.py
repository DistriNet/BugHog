from bughog.subject.state_oracle import StateOracle
from bughog.subject.webbrowser.base import Browser
from bughog.subject.webbrowser.firefox import repo
from bughog.subject.webbrowser.firefox.state_oracle import FirefoxStateOracle


class Firefox(Browser):
    @staticmethod
    def name() -> str:
        return 'firefox'

    @staticmethod
    def state_oracle() -> type[StateOracle]:
        return FirefoxStateOracle

    @staticmethod
    def get_availability() -> dict:
        return {
            'name': 'firefox',
            'min_version': 20,
            'max_version': repo.get_most_recent_major_version(),
        }
