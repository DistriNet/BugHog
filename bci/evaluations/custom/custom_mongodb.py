from bci.database.mongo.mongodb import MongoDB


class CustomMongoDB(MongoDB):

    def __init__(self):
        super().__init__()
        self.data_collection_names = {
            "chromium": "custom_chromium_data_test",
            "firefox": "custom_firefox_release_data_test"
        }

    def __get_data_collection(self, browser_name: str):
        collection_name = self.data_collection_names[browser_name]
        if collection_name not in self.db.collection_names():
            raise AttributeError("Collection '%s' not found in database" % collection_name)
        return self.db[collection_name]
