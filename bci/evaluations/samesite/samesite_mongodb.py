from bci.database.mongo.mongodb import MongoDB


class SamesiteMongoDB(MongoDB):

    def __init__(self):
        super().__init__()
        self.data_collection_names = {
            "chromium": "chromium_data",
            "firefox": "firefox_data"
        }

    def __get_data_collection(self, browser_name: str):
        collection_name = self.data_collection_names[browser_name]
        if collection_name not in self.db.collection_names():
            raise AttributeError("Collection '%s' not found in database" % collection_name)
        return self.db[collection_name]
