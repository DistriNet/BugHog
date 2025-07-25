import functools
from datetime import datetime, timedelta, timezone

from bughog.database.mongo.mongodb import MongoDB


class Cache:

    @staticmethod
    def cache_in_db(subject_type: str, subject_name: str, ttl: int = 0):
        """
        Caches the result of the function in MongoDB, with respect to TTL (in hours).
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if hasattr(func, '__self__') or (args and hasattr(args[0], func.__name__)):
                    key = args[1] if len(args) > 1 else kwargs.get('key')
                else:
                    key = args[0] if args else kwargs.get('key')

                collection = MongoDB().get_cache_collection(subject_type)
                doc = collection.find_one({
                    'subject_name': subject_name,
                    'function_name': func.__name__,
                    'key': key
                })

                now = datetime.now(timezone.utc)
                # Check for cache existence and TTL
                if doc and 'value' in doc and 'ts' in doc:
                    # If TTL is 0, cache is kept indefinitely
                    if ttl == 0:
                        return doc['value']
                    # Else, check whether cache has expired
                    try:
                        cached_time = datetime.fromisoformat(doc['ts'])
                    except Exception:
                        # Fallback in case of serialization issues
                        cached_time = datetime.strptime(doc['ts'], "%Y-%m-%d %H:%M:%S%z")
                    age = now - cached_time
                    if age < timedelta(hours=ttl):
                        return doc['value']

                new_value = func(*args, **kwargs)
                if new_value is not None:
                    collection.update_one(
                        {
                            'subject_name': subject_name,
                            'function_name': func.__name__,
                            'key': key,
                        },
                        {
                            '$set': {
                                'value': new_value,
                                'ts': now.replace(microsecond=0).isoformat(),
                            }
                        },
                        upsert=True
                    )
                return new_value
            return wrapper
        return decorator
