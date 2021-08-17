import json
import redis
from typing import Union, List


class RedisConnection(object):

    def __init__(self, decode_responses=True, *args, **kwargs):
        """
        Convenience wrapper class for redis. Passes all arguments directly to redis.

        :param decode_responses: defaults to True for convenience
        :param args: will be passed to redis.Redis()
        :param kwargs: will be passed to redis.Redis()
        """
        self.R = redis.Redis(decode_responses=decode_responses, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.R.close()

    def json_deserialize(self, s: Union[str, bytes]) -> Union[dict, bytes]:
        try:
            return json.loads(s)
        except json.decoder.JSONDecodeError:
            # just return the raw value in case we have a json decoding error
            return s

    def get_single(self, key: str) -> Union[dict, bytes]:
        """
        invokes redis get() method but tries to de-serialize the data to python object.

        :param key: name of the key
        :return: dict or bytes, depending on whether the de-serialization was successful
        """
        if v := self.R.get(key):
            return self.json_deserialize(v)
        else:
            return {}

    def get_multiple(self, keys: List[str]) -> list:
        """
        invokes get_single(key) for each key in keys.

        :param keys: list of keys
        :return: list of dicts
        """
        return [self.get_single(k) for k in keys]

    def get(self, key: Union[str, list]) -> Union[dict, list]:
        """
        wraps redis get() method, and takes care of de-serialization. kan handle one or multiple keys

        :param key: key or list of keys
        :return dict or list of dicts
        """

        if isinstance(key, str):
            return self.get_single(key)
        elif isinstance(key, list):
            return self.get_multiple(keys=key)
        else:
            raise TypeError("expects a key or a list of keys as parameter")

    def set(self, key: str, data: object) -> str:
        """
        invokes redis set() method but serializes python object to json first.

        :param key: name of the key
        :param data: a json-serializable python object
        :return str: key, name of the key
        """
        data = json.dumps(data)
        self.R.set(key, data)
        return key

    def get_keys(self, pattern: str) -> dict:
        """
        looks for keys that match ``pattern``, retrieve the data,
        and return a dictionary of the form key: data.

        :param pattern: key pattern that will be retrieved from redis
        :return dict: dictionary of the form key: data
        """
        keys = self.get_key_pattern(pattern)
        return {
            k: self.get(k)
            for k in keys
        }

    def get_key_pattern(self, pattern: str) -> list:
        """
        looks for all keys in redis that fulfil ``pattern``


        :param pattern: key pattern that will be retrieved from redis
        :return list: list of all keys that match the pattern
        """
        if not pattern.endswith('*'):
            pattern = f"{pattern}*"
        if keys := self.R.keys(pattern):
            return keys
        else:
            return []

    def get_data_for_keys(self, keys: list) -> list:
        """
        returns a list of values for all keys in ``keys``

        :param keys: list of keys
        :return list: list of retrieved data objects
        """
        return [self.get(k) for k in keys]

    def set_dict(self, data: dict) -> list:
        """
        saves each entry of a python dictionary as a seperate entry to redis,
        and returns a list of all the keys that were set.

        :param data: dictionary that should be set to redis
        :return list:
        """
        return [self.set(k, v) for k, v in data.items()]
