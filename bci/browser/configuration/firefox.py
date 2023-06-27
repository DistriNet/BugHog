import os

from bci import cli
from bci.browser.configuration.browser import Browser
from bci.browser.configuration.options import Default, BlockThirdPartyCookies, PrivateBrowsing, TrackingProtection
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

    def _get_terminal_args(self) -> list[str]:
        assert self._profile_path is not None

        args = [self._get_executable_file_path()]
        args.extend(['-profile', self._profile_path])
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
            self._profile_path = prepare_firefox_profile('default-67')

        # Make Firefox trust the proxy CA and server CA
        # cert9.db  key4.db  pkcs11.txt
        cli.execute(
            f'certutil -A -n bughog-ca -t CT,c -i /home/bci/bughog_ca.crt -d sql:{self._profile_path}'
            )
        # Normally: cert8.db  key3.db  secmod.db, however: cert9.db  key4.db  pkcs11.txt
        cli.execute(
            f'certutil -A -n bughog-ca -t CT,c -i /home/bci/bughog_ca.crt -d {self._profile_path}'
            )

        # The certutil in the docker image refuses to create cert8.db, so we copy
        # an existing cert8.db which accepts the necessary CAs
        cli.execute(f'cp /app/browser/profiles/firefox/cert8.db {self._profile_path}')
        # How to create a cert8.db?
        # Current certutils versions do not support creating cert8.db anymore.
        # However, older Firefox versions (<= 57) embed an old version the certutils library libnss3.so.
        # Use this by `LD_LIBRARY_PATH=firefox/libnss3.so certutil -A -n bughog-ca -t CT,c -i /home/bci/bughog_ca.crt -d dbm:.{self._profile_path}`.
        # Your cert8.db will be created in the current directory.
