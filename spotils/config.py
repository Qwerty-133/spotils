"""Allows accessing the JSON config values through classes."""
import json
import os
from importlib import resources

import platformdirs
from mergedeep import Strategy, merge

from spotils.helpers.nested_key_mapping import ConfigMapping
from spotils.type_aliases import JSONVals

DEFAULT_CONFIG_TRAVERSABLE = (
    resources.files(__package__) / "../config-default.json"
)
USER_CONFIG_PATH = (
    platformdirs.user_config_path(appname=__package__, appauthor=False)
    / "config.json"
)

default_config_data = ConfigMapping(
    json.loads(DEFAULT_CONFIG_TRAVERSABLE.read_text())
)
config_data = ConfigMapping(default_config_data)

try:
    with USER_CONFIG_PATH.open() as f:
        local_config_data = ConfigMapping(json.load(f))
except FileNotFoundError:
    os.makedirs(USER_CONFIG_PATH.parent, exist_ok=True)
    with USER_CONFIG_PATH.open("w") as f:
        json.dump({}, f)

    local_config_data = ConfigMapping()
else:
    merge(config_data, local_config_data, strategy=Strategy.TYPESAFE_REPLACE)


class JsonLoaderMeta(type):
    """Enables fetching JSON config values by attribute access."""

    def __getattr__(cls, name: str) -> JSONVals:
        """
        Use the class's section and subsection attributes to fetch vals.

        name: the name of the actual key to fetch
        The subsection is optional.
        """
        section_name = cls.section
        try:
            # Avoid infinite recursion
            subsection_name = object.__getattribute__(cls, "subsection")
        except AttributeError:
            keys = [section_name, name]
        else:
            keys = [section_name, subsection_name, name]
        return config_data[keys]


class JsonLoader(metaclass=JsonLoaderMeta):
    """
    Base JSON loader class, inherited by namespaces.

    The subclasses shouldn't be instantiated, but accessed as
    namespaces.
    """


class Spotify(JsonLoader):
    """Namespace for the Spotify config section."""

    section = "spotify"

    liked_songs_playlist_id: str


class LikedSongsSync(JsonLoader):
    """Namespace for the LikedSongsSync config section."""

    section = "tasks"
    subsection = "liked_songs_sync"

    enabled: bool
    short_sync_enabled: bool
    short_sync_interval: str
    short_sync_limit: int
    full_sync_interval: str


class SkipLikedSongs(JsonLoader):
    """Namespace for the SkipLikedSongs config section."""

    section = "tasks"
    subsection = "skip_liked_songs"

    enabled: bool
    interval: str


class Dev(JsonLoader):
    """Namespace for the Dev config section."""

    section = "dev"

    reset_playlist_id: str
    liked_songs_fetch_limit: int


def set_config_value(key_path: str, value: JSONVals) -> None:
    """Set a local config value and save it to the user config file."""
    parent_keys, _ = ConfigMapping.split_key(key_path)
    current = local_config_data
    for parent_key in parent_keys:
        if parent_key not in local_config_data:
            current[parent_key] = {}
        current = current[parent_key]

    local_config_data[key_path] = value
    with USER_CONFIG_PATH.open("w") as f:
        json.dump(local_config_data.data, f)


def unset_config_key(key_path: str) -> None:
    """
    Unset a local config value.

    The value's parent dictionaries are also removed if they're
    empty after removal.
    """
    del local_config_data[key_path]
    remaining_keys = key_path.split(".")[:-1]

    while remaining_keys:
        if not local_config_data[remaining_keys]:
            del local_config_data[remaining_keys]
            remaining_keys.pop()

    with USER_CONFIG_PATH.open("w") as f:
        json.dump(local_config_data.data, f)
