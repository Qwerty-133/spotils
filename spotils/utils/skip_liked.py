"""Skips currently playing songs if they're already liked."""
import typing as t

from spotils import instance
from spotils.models import PlaybackState, Track


def skip_if_liked() -> None:
    """
    Skip the current track if it's liked.

    Ignore the track if the user is playing their liked songs.
    """
    # FIXME: Don't skip tracks which were liked mid-playthrough
    # TODO: Use cached liked songs to handle duplicates
    state = instance.current_playback()
    satisfactory_conditions = (
        state
        and state.item
        and state.is_playing
        and state.context
        and state.context.type != "collection"
        and state.currently_playing_type == "track"
    )
    if not satisfactory_conditions:
        return

    state = t.cast(PlaybackState, state)
    state_item = t.cast(Track, state.item)

    track_id = state_item.id
    liked_data = instance.current_user_saved_tracks_contains([track_id])
    if liked_data[0]:
        instance.next_track(state.device.id)
