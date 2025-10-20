import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from pymongo import ASCENDING, DESCENDING

from bughog import util
from bughog.database.mongo.mongodb import MongoDB

logger = logging.getLogger(__name__)

BASE_URL = "https://bughog.distrinet-research.be/"


class PublicBrowserStateCache:
    @staticmethod
    def update() -> None:
        def safe_request_json_and_update(collection_name: str, transform=lambda x: x):
            url = BASE_URL + collection_name + ".json"
            try:
                result = util.request_json(url)["data"]
                if result is not None:
                    PublicBrowserStateCache.__update_collection(collection_name, transform(result))
            except util.ResourceNotFound:
                logger.warning(f"Could not update commit cache with resource at {url}")
            except Exception:
                logger.error(f"Could not update commit cache for {collection_name}", exc_info=True)

        executor = ThreadPoolExecutor()
        executor.submit(safe_request_json_and_update, "firefox_executable_availability", transform=lambda x: list(x.values()))
        executor.submit(safe_request_json_and_update, "firefox_release_base_revs")
        executor.submit(safe_request_json_and_update, "chromium_release_base_revs")
        executor.shutdown(wait=False)

    @staticmethod
    def __update_collection(collection_name: str, data: list) -> None:
        collection = MongoDB().get_collection(collection_name)
        if (n := len(data)) == collection.count_documents({}):
            logger.debug(f"{collection_name} is still up-to-date ({n} documents).")
        else:
            collection.delete_many({})
            collection.insert_many(data)
            logger.info(f"{collection_name} is updated ({len(data)} documents).")

    @staticmethod
    def firefox_get_commit_nb(commit_id: str) -> int:
        collection = MongoDB().get_collection("firefox_binary_availability")
        result = collection.find_one({"revision_id": commit_id}, {"revision_number": 1})
        if result is None or "revision_number" not in result:
            raise AttributeError(f"Could not find 'revision_number' in {result}")
        return result["revision_number"]

    @staticmethod
    def firefox_has_executable_for(commit_nb: Optional[int] = None, commit_id: Optional[str] = None) -> bool:
        collection = MongoDB().get_collection("firefox_binary_availability")
        if commit_nb:
            result = collection.find_one({"revision_number": commit_nb})
        elif commit_id:
            result = collection.find_one({"revision_number": commit_nb})
        else:
            raise AttributeError("No commit number or id was provided")
        return result is not None

    @staticmethod
    def firefox_get_executable_info(commit_id: str) -> Optional[dict]:
        collection = MongoDB().get_collection("firefox_binary_availability")
        return collection.find_one({"node": commit_id}, {"files_url": 1, "app_version": 1})

    @staticmethod
    def firefox_get_previous_and_next_commit_nb_with_executable(commit_nb: int) -> tuple[Optional[int], Optional[int]]:
        collection = MongoDB().get_collection("firefox_binary_availability")

        previous_commit_nbs = collection.find({"revision_number": {"$lt": commit_nb}}).sort({"revision_number": DESCENDING})
        previous_document = next(previous_commit_nbs, None)

        next_commit_nbs = collection.find({"revision_number": {"$gt": commit_nb}}).sort({"revision_number": ASCENDING})
        next_document = next(next_commit_nbs, None)

        return (
            previous_document["revision_number"] if previous_document else None,
            next_document["revision_number"] if next_document else None,
        )

    @staticmethod
    def firefox_get_commit_id(commit_nb: int) -> Optional[str]:
        collection = MongoDB().get_collection("firefox_binary_availability")
        result = collection.find_one({"revision_number": commit_nb})
        if result is None:
            return None
        return result.get("node", None)

    @staticmethod
    def __get_release_base_rev_collection(browser: str) -> str:
        match browser:
            case "chromium":
                return "chromium_release_base_revs"
            case "firefox":
                return "firefox_release_base_revs"
            case _:
                raise AttributeError(f"Could not get collection for browser {browser}")

    @staticmethod
    def is_tag(browser: str, tag: str) -> bool:
        collection = MongoDB().get_collection(PublicBrowserStateCache.__get_release_base_rev_collection(browser))
        n = collection.count_documents({"release_tag": tag})
        return n > 0

    @staticmethod
    def get_release_tag(browser: str, major_release_version: int) -> str:
        collection = MongoDB().get_collection(PublicBrowserStateCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one({"major_version": major_release_version}):
            return doc["release_tag"]
        raise AttributeError(f"Could not find release tag associated with version '{major_release_version}'")

    @staticmethod
    def get_release_commit_nb(browser: str, major_release_version: int) -> int:
        collection = MongoDB().get_collection(PublicBrowserStateCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one({"major_version": major_release_version}):
            return doc["revision_number"]
        raise AttributeError(f"Could not find major release version '{major_release_version}'")

    @staticmethod
    def get_release_commit_id(browser: str, major_release_version: int) -> str:
        collection = MongoDB().get_collection(PublicBrowserStateCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one({"major_version": major_release_version}):
            return doc["revision_id"]
        raise AttributeError(f"Could not find major release version '{major_release_version}'")

    @staticmethod
    def get_most_recent_major_version(browser: str) -> int:
        collection = MongoDB().get_collection(PublicBrowserStateCache.__get_release_base_rev_collection(browser))
        if doc := collection.find_one(sort=[("major_version", -1)]):
            return doc["major_version"]
        raise AttributeError("Could not find most recent major release version")
