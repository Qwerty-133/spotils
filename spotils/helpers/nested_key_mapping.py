"""A dictionary that allows nested key access with dot notation."""

import collections
import typing as t
from collections.abc import Mapping

from spotils.type_aliases import JSONVals

Key = t.Union[str, t.Iterable[str]]


class ConfigMapping(collections.UserDict, t.MutableMapping[str, JSONVals]):
    """
    A dictionary that allows nested key access with dot notation.

    Keys should only be strings.

    A list of keys can also be passed to access nested keys.
    map["foo.bar"] == map["foo"]["bar"] == map[["foo", "bar"]]

    Used for wrapping config data.
    """

    @staticmethod
    def split_key(key: Key) -> tuple[list[str], str]:
        """Split a key into a list of keys and the last key."""
        keys = list(ConfigMapping.get_keys(key))
        last_key = keys.pop()
        return keys, last_key

    @staticmethod
    def get_keys(key: Key) -> t.Iterable[str]:
        """Get the actual list of keys for a key."""
        if isinstance(key, str):
            return key.split(".")
        else:
            return key

    def resolve(self, key: Key) -> JSONVals:
        """Resolve a key to its value."""
        current = self.data
        for actual_key in self.get_keys(key):
            if not isinstance(current, Mapping):
                raise KeyError(actual_key)
            current = current[actual_key]
        return current

    def resolve_to_mapping(self, key: Key) -> t.MutableMapping[str, JSONVals]:
        """Resolve a key and ensure it's a mutable mapping."""
        value = self.resolve(key)
        if not isinstance(value, Mapping):
            raise TypeError(f"Expected {key} to be a mutable mapping.")
        return value

    def __getitem__(self, key: Key) -> JSONVals:
        return self.resolve(key)

    def __delitem__(self, key: Key) -> None:
        parent_keys, key = self.split_key(key)
        del self.resolve_to_mapping(parent_keys)[key]

    def __setitem__(self, key: Key, item: JSONVals) -> None:
        parent_keys, key = self.split_key(key)
        self.resolve_to_mapping(parent_keys)[key] = item

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.data!r})"

    def __contains__(self, key: Key) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True
