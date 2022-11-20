"""
A spotify client implementation which returns models upon API requests.

Subclasses spotipy.Spotify.
"""
import typing as t

from spotipy import Spotify

from spotils.models import Model, ModelableJSON, PlaybackState

MT = t.TypeVar("MT", bound=Model)


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
