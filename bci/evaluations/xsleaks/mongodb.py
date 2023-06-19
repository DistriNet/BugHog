import logging
from bci.database.mongo.mongodb import MongoDB


class XSLeaksMonogDB(MongoDB):

    def __init__(self):
        super().__init__()
        self.data_collection_names = {
            "chromium": "chromium_xsleaks_data",
            "firefox": "firefox_xsleaks_data"
        }

    @staticmethod
    def get_instance():
        if XSLeaksMonogDB.instance is None:
            XSLeaksMonogDB.instance = XSLeaksMonogDB()
        return XSLeaksMonogDB.instance

    def __get_data_collection(self, browser_name: str):
        collection_name = self.data_collection_names[browser_name]
        if collection_name not in self.db.collection_names():
            raise AttributeError("Collection '%s' not found in database" % collection_name)
        return self.db[collection_name]
