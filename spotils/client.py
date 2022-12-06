"""
A spotify client implementation which returns models upon API requests.

Subclasses spotipy.Spotify.
"""
import typing as t

import cachecontrol
import requests
import requests.adapters
import spotipy
import urllib3
from spotipy import Spotify

from spotils.models import (
    CurrentUser,
    Model,
    ModelableJSON,
    PagedModel,
    PlaybackState,
    PlaylistDetails,
    PlaylistTracks,
    Playlists,
    RecentlyPlayed,
    SavedTracks,
)

MT = t.TypeVar("MT", bound=Model)
PMT = t.TypeVar("PMT", bound=PagedModel)


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


class ModeledSpotify(Spotify):
    """A wrapper to spotipy.Spotify which returns data as Models."""

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """
        Initialize the client.

        Forwards args and kwargs to the super class, and initializes
        an attribute for storing cached user details.
        """
        super().__init__(*args, **kwargs)
        self.current_user_details: t.Optional[CurrentUser] = None

    # TODO: Override other methods for type-hinting arguments.
    @staticmethod
    def _optional_model(
        model: t.Type[MT], data: t.Optional[ModelableJSON]
    ) -> t.Optional[MT]:
        """
        Convert the data to a model if it's not None.

        None is returned if the data is None.
        """
        if data is not None:
            return model(data)

    @staticmethod
    def _casted_response(data: t.Any) -> ModelableJSON:
        """Cast the data to the ModelableJSON type."""
        return t.cast(ModelableJSON, data)

    def current_playback(self) -> t.Optional[PlaybackState]:
        """Get information about user's current playback."""
        response_data = self._casted_response(super().current_playback())
        return self._optional_model(PlaybackState, response_data)

    def current_user_recently_played(self, limit: int = 50) -> RecentlyPlayed:
        """Get the current user's recently played tracks."""
        response_data = self._casted_response(
            super().current_user_recently_played(limit)
        )
        return RecentlyPlayed(response_data)

    def current_user_saved_tracks(self) -> SavedTracks:
        """Get a list of the saved tracks of the current user."""
        response_data = self._casted_response(
            super().current_user_saved_tracks(50)
        )
        return SavedTracks(response_data)

    def next(self, model: PMT) -> t.Optional[PMT]:
        """Return the next result given a paged result."""
        if model.next is None:
            return None
        return self._optional_model(type(model), self._get(model.next))

    def playlist_tracks(self, playlist_id: str) -> PlaylistTracks:
        """Get full details of the tracks of a playlist."""
        response_data = self._casted_response(
            self.playlist_items(playlist_id, additional_types=("track",))
        )
        return PlaylistTracks(response_data)

    def playlist(self, playlist_id: str) -> PlaylistDetails:
        """
        Get playlist details by id.

        Only track items are fetched.
        """
        response_data = self._casted_response(
            super().playlist(playlist_id, additional_types=("track",))
        )
        return PlaylistDetails(response_data)

    def playlist_add_items(
        self,
        playlist_id: str,
        tracks: list[str],
        position: t.Optional[int] = None,
    ) -> str:
        """
        Add tracks/episodes to a playlist.

        The playlist's new snapshot id is returned.
        """
        response_data = self._casted_response(
            super().playlist_add_items(playlist_id, tracks, position)
        )
        return t.cast(str, response_data["snapshot_id"])

    def current_user_saved_tracks_contains(
        self, tracks: list[str]
    ) -> list[bool]:
        """Check if tracks are liked by the current user."""
        response_data = self._casted_response(
            super().current_user_saved_tracks_contains(tracks)
        )
        return t.cast(list[bool], response_data)

    def current_user_playlists(self) -> Playlists:
        """Get a list of the playlists of the current user."""
        response_data = self._casted_response(super().current_user_playlists())
        return Playlists(response_data)

    def current_user(self) -> CurrentUser:
        """
        Get detailed profile information about the current user.

        The information is cached.
        """
        if self.current_user_details is None:
            response_data = self._casted_response(super().current_user())
            self.current_user_details = CurrentUser(response_data)

        return self.current_user_details


class ResilientAdapter(cachecontrol.CacheControlAdapter):
    """
    An adapter which caches requests, and retries on errors.

    This adapter adds a timeout to each request.
    """

    MAX_TIMEOUT = 2
    DEFAULT_RETRY = urllib3.Retry(
        total=5,
        allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
        backoff_factor=0.3,
        status_forcelist=frozenset([500, 502, 503, 504]),
    )

    def __init__(
        self,
        *args: t.Any,
        max_timeout: t.Optional[float] = None,
        **kwargs: t.Any
    ) -> None:
        """
        Initialise the adapter.

        A max_timeout can be passed which applies to each request
        which defaults to MAX_TIMEOUT.
        If max_retries is not passed, it defaults to DEFAULT_RETRY.
        """
        kwargs.setdefault("max_retries", self.DEFAULT_RETRY)
        super().__init__(*args, **kwargs)
        self.max_timeout = max_timeout or self.MAX_TIMEOUT

    def send(self, *args: t.Any, **kwargs: t.Any) -> requests.Response:
        """
        Send a request.

        If no timeout is passed, apply the default timeout.
        """
        kwargs.setdefault("timeout", self.max_timeout)
        return super().send(*args, **kwargs)


global_session = requests.Session()
adapter = ResilientAdapter()
global_session.mount("http://", adapter)
global_session.mount("https://", adapter)


def generate_global_instance() -> ModeledSpotify:
    """
    Get an appropriate instance of ModeledSpotify.

    This instance is used throughout the application.
    """
    scopes = ",".join(SCOPES)

    # TODO: Let users configure whether the browser should be opened
    return ModeledSpotify(
        auth_manager=spotipy.SpotifyOAuth(
            scope=scopes, requests_session=global_session
        ),
        requests_session=global_session,
    )
