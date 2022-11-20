"""Initialises the global wrapper instance."""
import logging

import dotenv
import spotipy

from spotils.client import ModeledSpotify
from spotils.helpers.logging import InterceptHandler

dotenv.load_dotenv()

SCOPES = [
    "user-library-read",
    "user-modify-playback-state",
    "user-read-playback-state",
]

scopes = ",".join(SCOPES)
# TODO: Let users configure whether the browser should be opened
instance = ModeledSpotify(auth_manager=spotipy.SpotifyOAuth(scope=scopes))

logging.basicConfig(
    handlers=[InterceptHandler()], level=logging.INFO, force=True
)
