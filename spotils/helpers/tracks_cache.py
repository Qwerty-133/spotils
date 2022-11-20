"""Provides caches for caching playlist songs and liked songs."""
import threading
import time
import typing as t

from spotils import instance
from spotils.helpers.fetch_tracks import (
    lazy_fetch_tracks,
    lazy_fetch_tracks_from,
)
from spotils.models import Track


class PlaylistTracksCache:
    """
    A cache that stores the tracks in a given playlist.

    Snapshot ids are used to check if the playlist has changed.
    """

    def __init__(self, playlist_id: str) -> None:
        """Tracks are stored in the tracks attribute."""
        self.playlist_id = playlist_id
        self.tracks: list[Track] = []
        self.lock = threading.Lock()
        self.latest_snapshot_id: t.Optional[str] = None

    def sync_if_not_fresh(self, verify_validity: bool = True) -> None:
        """
        Sync the cache's tracks if the playlist has changed.

        If verify_validity is True, the snapshot id is checked again
        after syncing. If the playlist was changed while fetching,
        a ValueError is raised.
        """
        with self.lock:
            details = instance.playlist(self.playlist_id)
            if details.snapshot_id != self.latest_snapshot_id:
                self.tracks = list(lazy_fetch_tracks_from(details.tracks))
                self.latest_snapshot_id = details.snapshot_id

            if verify_validity:
                details = instance.playlist(self.playlist_id)
                if details.snapshot_id != self.latest_snapshot_id:
                    raise ValueError("Playlist changed while syncing.")


class LikedSongsCache:
    """A cache that stores the current liked songs of the user."""

    def __init__(self) -> None:
        """Tracks are stored in the tracks attribute."""
        self.tracks: list[Track] = []
        self.lock = threading.Lock()
        self.last_updated_at: t.Optional[float]

    def is_fresh(self, threshold: int) -> bool:
        """Return True if the cache was updated within the threshold."""
        with self.lock:
            if self.last_updated_at is None:
                return False

            return time.perf_counter() - self.last_updated_at < threshold

    def sync(self) -> None:
        """
        Sync the cache's tracks.

        last_updated_at is updated after syncing.
        """
        with self.lock:
            self.tracks = list(lazy_fetch_tracks())
            self.last_updated_at = time.perf_counter()

    def sync_if_not_fresh(self, threshold: int) -> None:
        """Sync the cache's tracks if it's not fresh."""
        with self.lock:
            if not self.is_fresh(threshold):
                self.sync()


liked_songs_cache = LikedSongsCache()
