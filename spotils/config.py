"""Allows accessing the JSON config values through classes."""
import json
import typing as t
from pathlib import Path

from mergedeep import Strategy, merge

DEFAULT_CONFIG_PATH = Path("config-default.json")
CONFIG_PATH = Path("config.json")

with DEFAULT_CONFIG_PATH.open() as f:
    config_data = json.load(f)

try:
    with CONFIG_PATH.open() as f:
        merge(config_data, json.load(f), strategy=Strategy.TYPESAFE_REPLACE)
except FileNotFoundError:
    pass


class JsonLoaderMeta(type):
    """Enables fetching JSON config values by attribute access."""

    def __getattr__(cls, name: str) -> t.Any:
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
            return config_data[section_name][name]
        else:
            return config_data[section_name][subsection_name][name]


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
