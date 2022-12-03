"""Removes empty "My Playlist #n" playlists from Spotify."""

import typing as t

from spotils import instance
from spotils.models import Playlists, SimplePlaylist


def lazy_fetch_playlists() -> t.Iterator[SimplePlaylist]:
    """Fetch all the playlists of the current user."""
    chunk = instance.current_user_playlists()
    yield from chunk.items

    while chunk.next:
        chunk = t.cast(Playlists, instance.next(chunk))
        yield from chunk.items


def run_cleanup() -> None:
    """
    Cleanup empty "My Playlist #n" playlists.

    Doesn't remove playlists that are not owned by the current user or
    ones that have a non-empty description.
    """
    for playlist in lazy_fetch_playlists():
        should_delete = (
            playlist.owner
            and playlist.owner.id == instance.current_user().id
            and playlist.name.startswith("My Playlist #")
            and playlist.tracks.total == 0
            and playlist.description is not None
            and playlist.description == ""
        )
        if should_delete:
            instance.current_user_unfollow_playlist(playlist.id)
