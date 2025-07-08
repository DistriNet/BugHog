import os
import re

from bughog import cli, util
from bughog.parameters import SubjectConfiguration
from bughog.subject.executable import Executable
from bughog.subject.webbrowser.profile import prepare_chromium_profile
from bughog.version_control.states.base import State

DEFAULT_FLAGS = [
    '--use-fake-ui-for-media-stream',
    '--ignore-certificate-errors',
    '--disable-background-networking',
    '--disable-client-side-phishing-detection',
    '--disable-component-update',
    '--disable-default-apps',
    '--disable-gpu',
    '--disable-hang-monitor',
    '--disable-popup-blocking',
    '--disable-prompt-on-repost',
    '--disable-sync',
    '--disable-web-resources',
    '--metrics-recording-only',
    '--no-first-run',
    '--password-store=basic',
    '--safebrowsing-disable-auto-update',
    '--use-mock-keychain',
    '--no-sandbox',
]


class ChromiumExecutable(Executable):
    def __init__(self, config: SubjectConfiguration, state: State) -> None:
        super().__init__(config, state)

    @property
    def executable_name(self) -> str:
        return 'chrome'

    def _get_version(self) -> str:
        command = f'./{self.executable_name} --version'
        output = cli.execute_and_return_output(command, cwd=self.executable_folder)
        match = re.match(r'Chromium (?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', output)
        if match:
            return match.group('version')
        raise AttributeError(f"Could not determine version of binary at '{self.executable_name}'.")

    def _configure_executable(self):
        # Remove unneccessary files
        locales_folder_path = os.path.join(self.executable_folder, 'locales')
        if os.path.isdir(locales_folder_path):
            util.remove_all_in_folder(locales_folder_path, except_files=['en-GB.pak', 'en-US.pak'])
        cli.execute_and_return_status(f'chmod -R a+x {self.executable_folder}')

    def get_navigation_sleep_duration(self) -> int:
        return 1

    def get_open_console_hotkey(self) -> list[str]:
        return ['ctrl', 'shift', 'j']

    def _get_terminal_args(self) -> list[str]:
        assert self._profile_path is not None

        args = [self.executable_path]
        args.append(f'--user-data-dir={self._profile_path}')
        args.append('--enable-logging')
        args.append('--v=1')
        args.append('--log-level=0')
        # Headless changed from version +/- 110 onwards: https://developer.chrome.com/docs/chromium/new-headless
        # Using the `--headless` flag will crash the browser for these later versions.
        # Also see: https://github.com/DistriNet/BugHog/issues/12
        # args.append('--headless=new')  # From Chrome

        if 'btpc' in self.config.subject_setting:
            # This is handled in the profile folder
            pass
        if 'pb' in self.config.subject_setting:
            args.append('--incognito')

        args.extend(self.config.cli_options)
        args.extend(DEFAULT_FLAGS)
        return args

    def _prepare_profile_folder(self):
        profile_path = None
        match self.config.subject_setting:
            case 'default':
                profile_path = prepare_chromium_profile()
            case 'btpc':
                if int(self.version) < 17:
                    profile_path = prepare_chromium_profile('6_btpc')
                elif int(self.version) < 24:
                    profile_path = prepare_chromium_profile('17_btpc')
                elif int(self.version) < 36:
                    profile_path = prepare_chromium_profile('24_btpc')
                elif int(self.version) < 40:
                    profile_path = prepare_chromium_profile('36_btpc')
                elif int(self.version) < 46:
                    profile_path = prepare_chromium_profile('40_btpc')
                elif int(self.version) < 59:
                    profile_path = prepare_chromium_profile('46_btpc')
                elif int(self.version) < 86:
                    profile_path = prepare_chromium_profile('59_btpc')
                else:
                    raise AttributeError('Chrome 86 and up not supported yet')
        self._profile_path = profile_path
