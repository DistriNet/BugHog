import os
import unittest

from bci.configuration import Global
import bci.browser.binary.vendors.chromium as chromium
import bci.browser.binary.vendors.firefox as firefox


class TestFolderAvailability(unittest.TestCase):

    @staticmethod
    def test_binaries_availability():
        assert os.path.isdir('/app/browser/binaries')

        assert os.path.isdir(chromium.BIN_FOLDER_PATH)
        assert os.path.isdir(os.path.join(chromium.BIN_FOLDER_PATH, 'artisanal'))
        assert os.path.isdir(os.path.join(chromium.BIN_FOLDER_PATH, 'downloaded'))

        assert os.path.isdir(firefox.BIN_FOLDER_PATH)
        assert os.path.isdir(os.path.join(firefox.BIN_FOLDER_PATH, 'artisanal'))
        assert os.path.isdir(os.path.join(firefox.BIN_FOLDER_PATH, 'downloaded'))

    @staticmethod
    def test_database_availability():
        assert os.path.isdir('/app/database/data')

    @staticmethod
    def test_experiments_availability():
        assert os.path.isdir('/app/experiments')

        assert os.path.isdir(Global.custom_page_folder)
        assert os.listdir(Global.custom_page_folder)

        assert os.path.isdir(Global.custom_test_folder)
        assert os.listdir(Global.custom_test_folder)

    @staticmethod
    def test_extensions_availability():
        assert os.path.isdir('/app/browser/extensions')
        assert os.path.isdir(chromium.EXTENSION_FOLDER_PATH)
        assert os.path.isdir(firefox.EXTENSION_FOLDER_PATH)

    @staticmethod
    def test_profiles_availability():
        assert os.path.isdir('/app/browser/profiles')
        assert os.listdir('/app/browser/profiles')

    @staticmethod
    def test_ssl_availability():
        assert os.path.isdir('/app/ssl')
        assert os.path.isfile('/app/ssl/bughog_ca.crt')
