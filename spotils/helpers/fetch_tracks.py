"""Helpers for fetching tracks from playlists and liked songs."""
import typing as t

from spotils import instance
from spotils.models import PlaylistTracks, SavedTracks, Track

TrackItems = t.Union[SavedTracks, PlaylistTracks]


def lazy_fetch_tracks_from(
    chunk: TrackItems, limit: t.Optional[int] = None
) -> t.Iterator[Track]:
    """Fetch the remaining tracks starting from the given chunk."""
    fetched = 0
    total = chunk.total

    for track_info in chunk.items:
        yield track_info.track
        fetched += 1
        if fetched == limit:
            return

    while chunk.next:
        chunk = t.cast(TrackItems, instance.next(chunk))

        if chunk.total != total:
            raise ValueError(
                "Total number of tracks changed while fetching the next batch."
            )

        for track_info in chunk.items:
            yield track_info.track
            fetched += 1
            if fetched == limit:
                return


def lazy_fetch_tracks(
    playlist_id: t.Optional[str] = None, limit: t.Optional[int] = None
) -> t.Iterator[Track]:
    """
    Fetch all the tracks from the playlist or liked songs.

    If playlist_id is None, liked songs are fetched.
    """
    if playlist_id is None:
        tracks = instance.current_user_saved_tracks()
    else:
        tracks = instance.playlist_tracks(playlist_id)

    yield from lazy_fetch_tracks_from(tracks, limit)
