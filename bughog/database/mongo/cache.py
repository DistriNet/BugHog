import functools
from datetime import datetime, timezone

from bughog.database.mongo.mongodb import MongoDB


class Cache:

    @staticmethod
    def cache_in_db(subject_type: str, subject_name: str):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(key):
                collection = MongoDB().get_cache_collection(subject_type)
                doc = collection.find_one({
                    'subject_name': subject_name,
                    'function_name': func.__name__,
                    'key': key
                })
                if doc and 'value' in doc:
                    return doc['value']

                new_value = func(key)
                if new_value is not None:
                    collection.insert_one({
                        'subject_name': subject_name,
                        'key': key,
                        'value': new_value,
                        'ts': str(datetime.now(timezone.utc).replace(microsecond=0)),
                    })
                return new_value
            return wrapper
        return decorator
