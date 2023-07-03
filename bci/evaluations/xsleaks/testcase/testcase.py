import json
import time
import logging
import os.path
from abc import abstractmethod
from bci import cli
from bci import util
from bci.version_control.states.state import State


class TestCase:

    REPORTS_FOLDER = "/reports"

    def __init__(self, browser: str, browser_version: str, mech_id: str, browser_binary: str,
                 state: State):
        self.logger = logging.getLogger("bci")
        self.browser = browser
        self.browser_version = browser_version
        self.mech_id = mech_id
        self.browser_binary = browser_binary
        self.state = state
        self.profile_path: str = ""

    @abstractmethod
    def run(self):
        pass

    def get_new_profile(self):
        if self.profile_path is not None:
            util.rmtree(self.profile_path)
        self.profile_path = Jar.increment_until_original("/tmp/new-profile")
        cli.execute("mkdir -p %s" % self.profile_path)
        if self.browser == "chromium":
            pass
        elif self.browser == "firefox":
            # Make Firefox trust the proxy CA and server CA
            # cert9.db  key4.db  pkcs11.txt
            cli.execute(
                "certutil -A -n littleproxy -t CT,c -i /app/ssl/LittleProxy_MITM.cer -d sql:%s" % self.profile_path)
            # Normally: cert8.db  key3.db  secmod.db, however: cert9.db  key4.db  pkcs11.txt
            cli.execute(
                "certutil -A -n littleproxy -t CT,c -i /app/ssl/LittleProxy_MITM.cer -d %s" % self.profile_path)
            # cert9.db  key4.db  pkcs11.txt
            cli.execute(
                "certutil -A -n myCA -t CT,c -i /app/ssl/myCA.crt -d sql:%s" % self.profile_path)
            # Normally: cert8.db  key3.db  secmod.db, however: cert9.db  key4.db  pkcs11.txt
            cli.execute(
                "certutil -A -n myCA -t CT,c -i /app/ssl/myCA.crt -d %s" % self.profile_path)
            # The certutil in the docker image refuses to create cert8.db, so we copy
            # an existing cert8.db which accepts the necessary CAs
            cli.execute("cp /app/browser/profiles/firefox/cert8.db %s" % self.profile_path)

    def visit(self, url: str, clean_profile=True, sleep_after_visit=20):
        self.logger.info("Visiting '%s' %s a clean profile" % (url, "with" if clean_profile or self.profile_path is None else "without"))
        if self.profile_path == "" or clean_profile:
            self.get_new_profile()
        if self.browser == "chromium":
            command = "%s --no-sandbox --disable-component-update --disable-popup-blocking --ignore-certificate-errors \
                --enable-logging --v=1 --user-data-dir=%s %s" % (self.browser_binary, self.profile_path, url)
        elif self.browser == "firefox":
            prefs_path = os.path.join(self.profile_path, "prefs.js")
            with open(prefs_path, "w") as file:
                file.write('user_pref("app.update.enabled", false);\n')
                file.write('user_pref("dom.disable_open_during_load", false);\n')
            command = "%s -profile %s %s" % (self.browser_binary, self.profile_path, url)
        else:
            raise AttributeError("Unknown browser '%s'" % self.browser)
        self.logger.info("Executing command '%s'" % command)
        cli.execute_as_daemon(command)

        time.sleep(sleep_after_visit)
        command = "pkill -SIGINT %s" % ("chrome" if self.browser == "chromium" else "firefox")
        self.logger.info("Executing command '%s'" % command)
        cli.execute_and_return_status(command)
        time.sleep(3)
        command = "pkill -SIGINT %s" % ("chrome" if self.browser == "chromium" else "firefox")
        self.logger.info("Executing command '%s'" % command)
        cli.execute_and_return_status(command)
        time.sleep(3)
        command = "pkill -o dbus-launch"
        self.logger.info("Executing command '%s'" % command)
        cli.execute_and_return_status(command)
        time.sleep(1)

    @staticmethod
    def read_report(file_name: str, remove_after=True):
        path = os.path.join(TestCase.REPORTS_FOLDER, file_name)
        if not os.path.isfile(path):
            return None
        with open(path, "r") as file:
            report = json.load(file)
        if remove_after:
            cli.execute("rm %s" % path)
        return report
