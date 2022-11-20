"""
A spotify client implementation which returns models upon API requests.

Subclasses spotipy.Spotify.
"""
import typing as t

from spotipy import Spotify

from spotils.models import (
    Model,
    ModelableJSON,
    PagedModel,
    PlaybackState,
    PlaylistDetails,
    PlaylistTracks,
    RecentlyPlayed,
    SavedTracks,
)

MT = t.TypeVar("MT", bound=Model)
PMT = t.TypeVar("PMT", bound=PagedModel)


class ModeledSpotify(Spotify):
    """A wrapper to spotipy.Spotify which returns data as Models."""

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
