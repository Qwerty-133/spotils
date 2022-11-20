"""Mirrors the currently liked songs into a different playlist."""
import difflib
import itertools
import threading
import typing as t

from spotils import config, instance
from spotils.helpers.fetch_tracks import lazy_fetch_tracks
from spotils.helpers.tracks_cache import PlaylistTracksCache, liked_songs_cache
from spotils.models import Track


class LikedSongsSyncer:
    """
    Handles the mirroring of liked songs to a different playlist.

    The playlist id is fetched from the config.
    Every instance of this syncer is thread safe, so when dealing with
    multiple threads it's recommended to only use a single instance.
    """

    def __init__(self) -> None:
        """
        Initialise the syncer.

        sync_lock is aquired during ongoing syncs.
        current_snapshot_id holds the latest snapshot id obtained after
        inserting a track.
        playlist_songs & liked_songs hold the current state of the
        respective caches for use in the various methods that
        manipulate the playlist.
        They're only in use while syncing.
        """
        self.current_snapshot_id = None
        self.sync_lock = threading.Lock()
        self.playlist_cache = PlaylistTracksCache(
            config.Spotify.liked_songs_playlist_id
        )
        self.playlist_songs: list[Track] = []
        self.liked_songs: list[Track] = []

    def populate_tracks(self, limit: t.Optional[int] = None) -> None:
        """
        Populate the liked songs and liked songs caches.

        A limit is supplied for short syncs, in which case the cache's
        aren't updated.
        """
        if limit is None:
            liked_songs_cache.sync()
            self.playlist_cache.sync_if_not_fresh()
            self.liked_songs = liked_songs_cache.tracks.copy()
            self.playlist_songs = self.playlist_cache.tracks.copy()
        else:
            self.liked_songs = list(lazy_fetch_tracks(limit=limit))
            self.playlist_songs = list(
                lazy_fetch_tracks(
                    config.Spotify.liked_songs_playlist_id, limit=limit
                )
            )

    @staticmethod
    def _get_corrected_opcodes(
        a: t.Sequence[t.Hashable], b: t.Sequence[t.Hashable]
    ) -> t.Iterator[tuple[str, int, int, int, int]]:
        """
        Fix the indexes returned by SequenceMatcher.get_opcodes.

        This function assumes that you are updating sequence a based on
        the produced opcodes. And thus subsequent indexes are updated
        based on the state of a.
        """
        matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        delta = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            yield (tag, i1 + delta, i2 + delta, j1, j2)
            if tag == "delete":
                delta -= i2 - i1
            elif tag == "insert":
                delta += j2 - j1
            elif tag == "replace":
                delta -= i2 - i1
                delta += j2 - j1

    def chunked_insert(self, p_start: int, l_start: int, l_end: int) -> None:
        """
        Insert liked_songs items from l_start to l_end at p_start.

        Insertions are done in chunks.
        playlist_songs is updated to reflect the new state.
        current_snapshot_id is updated to the newly returned snapshot
        id.
        """
        to_insert = self.liked_songs[l_start:l_end]
        iterators = [iter(to_insert)] * 100

        insertion_position = p_start

        for chunk in itertools.zip_longest(*iterators, fillvalue=None):
            track_ids = [track.id for track in chunk if track]

            self.current_snapshot_id = instance.playlist_add_items(
                config.Spotify.liked_songs_playlist_id,
                track_ids,
                insertion_position,
            )
            # FIXME: snapshot ids don't work when deleting subsequently
            #  from the same snapshot id. Might need to fix
            # indexes in that case. As such, we shouldn't use
            # snapshot ids in deletions.
            self.current_snapshot_id = None
            insertion_position += len(track_ids)

        self.playlist_songs[p_start:p_start] = to_insert

    def chunked_delete(self, p_start: int, p_end: int) -> None:
        """
        Delete playlist_songs items from p_start to p_end.

        Deletions are done in chunks.
        The current_snapshot_id is used for performing the deletion
        on the last insertion state.
        playlist_songs is updated to reflect the new state.
        """
        iterators = [iter(self.playlist_songs[p_start:p_end])] * 100

        for chunk in itertools.zip_longest(*iterators, fillvalue=None):
            data = []
            for ahead_by, track in enumerate(filter(None, chunk)):
                data.append(
                    {"uri": track.id, "positions": [p_start + ahead_by]}
                )
            instance.playlist_remove_specific_occurrences_of_items(
                config.Spotify.liked_songs_playlist_id,
                data,
                self.current_snapshot_id,
            )

        del self.playlist_songs[p_start:p_end]

    def chunked_replace(
        self, p_start: int, p_end: int, l_start: int, l_end: int
    ) -> None:
        """
        Replace playlist_songs items with liked_songs items.

        playlist_songs items from p_start to p_end are replaced by
        liked_songs items from l_start to l_end.

        Operations are performed in chunks.
        playlist_songs is updated to reflect the new state.
        """
        self.chunked_delete(p_start, p_end)
        self.chunked_insert(p_start, l_start, l_end)

    def _sync_playlist(self, limit: t.Optional[int] = None) -> None:
        """
        Perform operations to sync the target playlist with liked songs.

        By the end of this, playlist_songs and liked_songs are equal.
        """
        self.populate_tracks(limit)

        for tag, i1, i2, j1, j2 in self._get_corrected_opcodes(
            self.playlist_songs, self.liked_songs
        ):
            if tag == "replace":
                self.chunked_replace(i1, i2, j1, j2)
            elif tag == "delete":
                self.chunked_delete(i1, i2)
            elif tag == "insert":
                self.chunked_insert(i1, j1, j2)

        self.current_snapshot_id = None

    def sync_playlist(self, limit: t.Optional[int] = None) -> None:
        """
        Perform operations to sync the target playlist with liked songs.

        A different thread can't sync at the same time.
        By the end of this, playlist_songs and liked_songs are equal.
        """
        with self.sync_lock:
            self._sync_playlist(limit)
