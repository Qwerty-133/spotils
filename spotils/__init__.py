"""Initialises the global instance & console and setups logging."""

import logging
from importlib.metadata import metadata

import dotenv
import spotipy
from rich.console import Console

from spotils.client import ModeledSpotify
from spotils.helpers.logging import InterceptHandler

package_metadata = metadata(__package__)
__version__ = package_metadata["version"]
__app_name__ = package_metadata["name"]


dotenv.load_dotenv()

SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-library-read",
    "user-modify-playback-state",
    "user-read-playback-state",
    "user-read-recently-played",
]

scopes = ",".join(SCOPES)
# TODO: Let users configure whether the browser should be opened
instance = ModeledSpotify(auth_manager=spotipy.SpotifyOAuth(scope=scopes))

console = Console()

logging.basicConfig(
    handlers=[InterceptHandler()], level=logging.INFO, force=True
)
