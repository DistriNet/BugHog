import os
import re

from bughog import cli
from bughog.parameters import SubjectConfiguration
from bughog.subject.web_browser.executable import BrowserExecutable
from bughog.subject.web_browser.profile import prepare_firefox_profile, remove_profile_execution_folder
from bughog.version_control.state.base import State

SELENIUM_USED_FLAGS = ['--no-remote', '--new-instance']


class FirefoxExecutable(BrowserExecutable):
    def __init__(self, config: SubjectConfiguration, state: State) -> None:
        super().__init__(config, state)
        self._profile_path = None

    @property
    def executable_name(self) -> str:
        return 'firefox'

    def _get_version(self):
        command = './firefox --version'
        output = cli.execute_and_return_output(command, cwd=self.staging_folder)
        match = re.match(r'Mozilla Firefox (?P<version>[0-9]+)\.[0-9]+.*', output)
        if match:
            return match.group('version')
        raise AttributeError(f"Could not determine version of binary at '{self.executable_name}'.")

    def _optimize_for_storage(self) -> None:
        pass

    def _configure_executable(self):
        cli.execute_and_return_status(f'chmod -R a+x {self.staging_folder}')
        cli.execute_and_return_status(f'chmod -R a+w {self.staging_folder}')
        # Add policy.json to prevent updating. (this measure is effective from version 60)
        # https://github.com/mozilla/policy-templates/blob/master/README.md
        # (For earlier versions, the prefs.js file is used)
        distributions_path = os.path.join(self.staging_folder, 'distribution')
        os.makedirs(distributions_path, exist_ok=True)
        policies_path = os.path.join(distributions_path, 'policies.json')
        with open(policies_path, 'a') as file:
            file.write('{ "policies": { "DisableAppUpdate": true } }')

    @property
    def post_experiment_sleep_duration(self) -> int:
        return 2

    @property
    def open_console_hotkey(self) -> list[str]:
        return ['ctrl', 'shift', 'k']

    @property
    def supported_options(self) -> list[str]:
        return []

    def _get_cli_command(self) -> list[str]:
        assert self._profile_path is not None

        args = [self.executable_path]
        args.extend(['-profile', self._profile_path])
        args.append('-setDefaultBrowser')
        user_prefs = []

        def add_user_pref(key: str, value: str | int | bool):
            if isinstance(value, str):
                user_prefs.append(f'user_pref("{key}", "{value}");'.lower())
            else:
                user_prefs.append(f'user_pref("{key}", {value});'.lower())

        add_user_pref('app.update.enabled', False)
        add_user_pref('browser.shell.checkDefaultBrowser', False)
        if 'default' in self.config.subject_setting:
            pass
        elif 'btpc' in self.config.subject_setting:
            add_user_pref('network.cookie.cookieBehavior', 1)
            add_user_pref('browser.contentblocking.category', 'custom')
        elif 'tp' in self.config.subject_setting:
            if int(self.version) >= 65:
                add_user_pref('privacy.trackingprotection.enabled', True)
                add_user_pref('pref.privacy.disable_button.change_blocklis', False)
                add_user_pref('pref.privacy.disable_button.tracking_protection_exceptions', False)
                add_user_pref('urlclassifier.trackingTable', 'test-track-simple,base-track-digest256,content-track-digest256')
            else:
                add_user_pref('privacy.contentblocking.category', 'strict')
                add_user_pref('privacy.trackingprotection.enabled', True)
                add_user_pref('privacy.trackingprotection.socialtracking.enabled', True)
                add_user_pref('network.cookie.cookieBehavior', True)
                add_user_pref('pref.privacy.disable_button.tracking_protection_exceptions', True)
        elif 'no-tp' in self.config.subject_setting:
            add_user_pref('network.cookie.cookieBehavior', 0)
            add_user_pref('browser.contentblocking.category', 'custom')
            add_user_pref('privacy.trackingprotection.cryptomining.enabled', False)
            add_user_pref('privacy.trackingprotection.fingerprinting.enabled', False)
            add_user_pref('privacy.trackingprotection.pbmode.enabled', False)
        elif 'pb' in self.config.subject_setting:
            args.append('-private')
        elif 'allow-java-applets' in self.config.subject_setting:
            add_user_pref('plugin.state.java', 2)
        else:
            raise NotImplementedError()

        if self.config.extensions:
            raise AttributeError('Not implemented')

        args.extend(self.config.cli_options)
        args.extend(SELENIUM_USED_FLAGS)
        self.__create_prefs_file(user_prefs)
        return args

    def __create_prefs_file(self, user_prefs: list[str]):
        if self._profile_path:
            with open(os.path.join(self._profile_path, 'prefs.js'), 'a') as file:
                file.write('\n'.join(user_prefs))

    def _prepare_profile_folder(self):
        # TODO: double check validity of Firefox profiles
        if 'tp' in self.config.subject_setting:
            self._profile_path = prepare_firefox_profile('tp-67')
        else:
            self._profile_path = prepare_firefox_profile()

        # Make Firefox trust the bughog CA

        # For newer Firefox versions (> 57):
        # Generate SQLite database: cert9.db  key4.db  pkcs11.txt
        cli.execute(f'certutil -A -n bughog-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d sql:{self._profile_path}')
        # For older Firefox versions (<= 57):
        # Generate in Berkeley DB database: cert8.db, key3.db, secmod.db
        cli.execute(f'certutil -A -n bughog-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d dbm:{self._profile_path}')

        # More info:
        # - https://support.mozilla.org/en-US/questions/1207165
        # - https://stackoverflow.com/questions/1435000/programmatically-install-certificate-into-mozilla
        # - https://ftpdocs.broadcom.com/cadocs/0/CA%20SiteMinder%20r12%20SP3-ENU/Bookshelf_Files/HTML/idocs/792390.html

    def _remove_profile_folder(self):
        if self._profile_path:
            remove_profile_execution_folder(self._profile_path)
