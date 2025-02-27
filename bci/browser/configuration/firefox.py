import os

from bci import cli
from bci.browser.configuration.browser import Browser
from bci.browser.configuration.options import BlockThirdPartyCookies, Default, PrivateBrowsing, TrackingProtection
from bci.browser.configuration.profile import prepare_firefox_profile

SUPPORTED_OPTIONS = [
    Default(),
    BlockThirdPartyCookies(),
    PrivateBrowsing(),
    TrackingProtection()
]

SELENIUM_USED_FLAGS = [
    '--no-remote',
    '--new-instance'
]


class Firefox(Browser):

    def get_navigation_sleep_duration(self) -> int:
        return 2

    def get_open_console_hotkey(self) -> list[str]:
        return ["ctrl", "shift", "k"]

    def _get_terminal_args(self) -> list[str]:
        assert self._profile_path is not None

        args = [self._get_executable_file_path()]
        args.extend(['-profile', self._profile_path])
        args.append('-setDefaultBrowser')
        user_prefs = []

        def add_user_pref(key: str, value: str | int | bool):
            if isinstance(value, str):
                user_prefs.append(f'user_pref("{key}", "{value}");'.lower())
            else:
                user_prefs.append(f'user_pref("{key}", {value});'.lower())

        # add_user_pref('network.proxy.ftp', proxy.HOST)
        # add_user_pref('network.proxy.ftp_port', proxy.PORT)
        # add_user_pref('network.proxy.http', proxy.HOST)
        # add_user_pref('network.proxy.http_port', proxy.PORT)
        # add_user_pref('network.proxy.socks', proxy.HOST)
        # add_user_pref('network.proxy.socks_port', proxy.PORT)
        # add_user_pref('network.proxy.ssl', proxy.HOST)
        # add_user_pref('network.proxy.ssl_port', proxy.PORT)
        # add_user_pref('network.proxy.type', 1)

        add_user_pref('app.update.enabled', False)
        add_user_pref('browser.shell.checkDefaultBrowser', False)
        if 'default' in self.browser_config.browser_setting:
            pass
        elif 'btpc' in self.browser_config.browser_setting:
            add_user_pref('network.cookie.cookieBehavior', 1)
            add_user_pref('browser.contentblocking.category', 'custom')
        elif 'tp' in self.browser_config.browser_setting:
            if self.version >= 65:
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
        elif 'no-tp' in self.browser_config.browser_setting:
            add_user_pref('network.cookie.cookieBehavior', 0)
            add_user_pref('browser.contentblocking.category', 'custom')
            add_user_pref('privacy.trackingprotection.cryptomining.enabled', False)
            add_user_pref('privacy.trackingprotection.fingerprinting.enabled', False)
            add_user_pref('privacy.trackingprotection.pbmode.enabled', False)
        elif 'pb' in self.browser_config.browser_setting:
            args.append('-private')
        elif 'allow-java-applets' in self.browser_config.browser_setting:
            add_user_pref('plugin.state.java', 2)
        else:
            raise NotImplementedError()

        if self.browser_config.extensions:
            raise AttributeError("Not implemented")

        args.extend(self.browser_config.cli_options)
        args.extend(SELENIUM_USED_FLAGS)
        self.__create_prefs_file(user_prefs)
        return args

    def __create_prefs_file(self, user_prefs: list[str]):
        with open(os.path.join(self._profile_path, 'prefs.js'), 'a') as file:
            file.write('\n'.join(user_prefs))

    def _prepare_profile_folder(self):
        # TODO: double check validity of Firefox profiles
        if 'tp' in self.browser_config.browser_setting:
            self._profile_path = prepare_firefox_profile('tp-67')
        else:
            self._profile_path = prepare_firefox_profile()

        # Make Firefox trust the bughog CA

        # For newer Firefox versions (> 57):
        # Generate SQLite database: cert9.db  key4.db  pkcs11.txt
        cli.execute(
            f'certutil -A -n bughog-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d sql:{self._profile_path}'
            )
        # For older Firefox versions (<= 57):
        # Generate in Berkeley DB database: cert8.db, key3.db, secmod.db
        cli.execute(
            f'certutil -A -n bughog-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d dbm:{self._profile_path}'
            )

        # More info:
        # - https://support.mozilla.org/en-US/questions/1207165
        # - https://stackoverflow.com/questions/1435000/programmatically-install-certificate-into-mozilla
        # - https://ftpdocs.broadcom.com/cadocs/0/CA%20SiteMinder%20r12%20SP3-ENU/Bookshelf_Files/HTML/idocs/792390.html
