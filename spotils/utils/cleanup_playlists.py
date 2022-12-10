"""Removes empty "My Playlist #n" playlists from Spotify."""

import typing as t

from spotils import instance
from spotils.models import Playlists, SimplePlaylist


def fetch_playlists() -> list[SimplePlaylist]:
    """Fetch all the playlists of the current user."""
    playlists: list[SimplePlaylist] = []
    chunk = instance.current_user_playlists()
    playlists.extend(chunk.items)

    while chunk.next:
        chunk = t.cast(Playlists, instance.next(chunk))
        playlists.extend(chunk.items)

    return playlists


def run_cleanup() -> None:
    """
    Cleanup empty "My Playlist #n" playlists.

    Doesn't remove playlists that are not owned by the current user or
    ones that have a non-empty description.
    """
    for playlist in fetch_playlists():
        should_delete = (
            playlist.owner
            and playlist.owner.id == instance.current_user().id
            and playlist.name.startswith("My Playlist #")
            and playlist.tracks.total == 0
            and playlist.description == ""
        )
        if should_delete:
            instance.current_user_unfollow_playlist(playlist.id)
