from bci.browser.configuration.browser import Browser
from bci.browser.configuration.options import Default, BlockThirdPartyCookies, PrivateBrowsing
from bci.browser.configuration.profile import prepare_chromium_profile

SUPPORTED_OPTIONS = [
    Default(),
    BlockThirdPartyCookies(),
    PrivateBrowsing()
]

SELENIUM_USED_FLAGS = [
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


class Chromium(Browser):

    def _get_terminal_args(self) -> list[str]:
        assert self._profile_path is not None

        args = [self._get_executable_file_path()]
        args.append(f'--user-data-dir={self._profile_path}')
        # Enable logging
        args.append('--enable-logging')
        args.append('--v=1')
        args.append('--log-level=0')
        # Headless changed from version +/- 110 onwards: https://developer.chrome.com/docs/chromium/new-headless
        # Using the `--headless` flag will crash the browser for these later versions.
        # Also see: https://github.com/DistriNet/BugHog/issues/12
        # args.append('--headless=new')  # From Chrome

        if 'btpc' in self.browser_config.browser_setting:
            # This is handled in the profile folder
            pass
        if 'pb' in self.browser_config.browser_setting:
            args.append('--incognito')

        if self.browser_config.extensions:
            raise AttributeError("Not implemented")

        # Proxy settings
        # args.append(f'--proxy-server=ftp={proxy.HOST}:{proxy.PORT};http={proxy.HOST}:{proxy.PORT};https={proxy.HOST}:{proxy.PORT}')
        # os.environ['http.proxyHost'] = proxy.HOST
        # os.environ['http.proxyPort'] = str(proxy.PORT)

        args.extend(self.browser_config.cli_options)
        args.extend(SELENIUM_USED_FLAGS)
        return args

    def _prepare_profile_folder(self):
        profile_path = None
        match self.browser_config.browser_setting:
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
                    raise AttributeError("Chrome 86 and up not supported yet")
        self._profile_path = profile_path
