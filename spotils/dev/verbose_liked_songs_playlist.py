"""
Assists development of the liked_songs_sync util.

config.Dev.reset_playlist_id should have tracks that the liked songs
playlist should contain before it's synced with the actual liked songs.
"""
import difflib
import itertools
import typing as t

from spotils import config, console, instance
from spotils.helpers.fetch_tracks import lazy_fetch_tracks
from spotils.models import Track


class LikedSongsSyncer:
    def __init__(self) -> None:
        self.current_snapshot_id = None
        self.playlist_songs: list[Track] = []
        self.liked_songs: list[Track] = []

    def fetch_all_tracks(
        self, playlist_id: t.Optional[str] = None
    ) -> list[Track]:
        return list(lazy_fetch_tracks(playlist_id))

    def populate_tracks(self, debug=False) -> None:
        if debug:
            self.insertion_id = config.Spotify.liked_songs_playlist_id
            self.playlist_songs = self.fetch_all_tracks(self.insertion_id)
            self.liked_songs = self.fetch_all_tracks(
                config.Dev.reset_playlist_id
            )
            return
        self.insertion_id = config.Spotify.liked_songs_playlist_id
        self.playlist_songs = self.fetch_all_tracks(
            config.Spotify.liked_songs_playlist_id
        )
        self.liked_songs = self.fetch_all_tracks()

    @staticmethod
    def _get_corrected_opcodes(
        a, b
    ) -> t.Iterator[tuple[str, int, int, int, int]]:
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
        to_insert = self.liked_songs[l_start:l_end]
        iterators = [iter(to_insert)] * 100

        insertion_position = p_start

        for chunk in itertools.zip_longest(*iterators, fillvalue=None):
            tracks = [track.id for track in chunk if track]
            self.current_snapshot_id = instance.playlist_add_items(
                self.insertion_id, tracks, insertion_position
            )
            self.current_snapshot_id = None
            insertion_position += len(tracks)

        self.playlist_songs[p_start:p_start] = to_insert

    def chunked_delete(self, p_start: int, p_end: int) -> None:
        iterators = [iter(self.playlist_songs[p_start:p_end])] * 100

        for chunk in itertools.zip_longest(*iterators, fillvalue=None):
            data = []
            for ahead_by, track in enumerate(filter(None, chunk)):
                data.append(
                    {"uri": track.id, "positions": [p_start + ahead_by]}
                )
            instance.playlist_remove_specific_occurrences_of_items(
                self.insertion_id, data, self.current_snapshot_id
            )

        del self.playlist_songs[p_start:p_end]

    def chunked_replace(
        self, p_start: int, p_end: int, l_start: int, l_end: int
    ) -> None:
        self.chunked_delete(p_start, p_end)
        self.chunked_insert(p_start, l_start, l_end)

    def debug_sync_playlist(self) -> None:
        self.populate_tracks(debug=True)
        self.sync_playlist()
        self.populate_tracks()
        self.sync_playlist()

    def sync_playlist(self) -> None:
        # self.populate_tracks()

        for tag, i1, i2, j1, j2 in self._get_corrected_opcodes(
            self.playlist_songs, self.liked_songs
        ):
            first = f"{i1+1}[dim]->[/]{i2}" if i1 + 1 != i2 else f"{i1+1}"
            second = f"{j1+1}[dim]->[/]{j2}" if j1 + 1 != j2 else f"{j1+1}"
            if tag == "replace":
                console.print(f"[blue]{tag}[/] {first} with {second}")
                self.chunked_replace(i1, i2, j1, j2)
                start = i1 - 2
                end = i2 - (i2 - i1) + (j2 - j1) + 2
                new_start = i1
                new_end = i1 + (j2 - j1)

            elif tag == "delete":
                console.print(f"[red]{tag}[/] {first}")
                self.chunked_delete(i1, i2)
                start = i1 - 3
                end = i2 - (i2 - i1) + 2
                new_start = new_end = -1

            elif tag == "insert":
                console.print(f"[green]{tag}[/] {second} at {i1+1}")
                self.chunked_insert(i1, j1, j2)
                start = i1 - 2
                end = i1 + (j2 - j1) + 2
                new_start = i1
                new_end = i1 + (j2 - j1)
            else:
                continue

            start -= 5
            end += 5

            fixed_start = max(0, start)
            fixed_end = min(len(self.playlist_songs), end)
            fixed_new_start = max(0, new_start)
            fixed_new_end = min(len(self.playlist_songs), new_end)

            strings = []
            for index in range(fixed_start, fixed_end):
                element = self.playlist_songs[index]
                if index in range(fixed_new_start, fixed_new_end):
                    strings.append(f"[green]{element.name}[/]")
                else:
                    strings.append(f"[blue][dim]{element.name}[/][/]")
            console.print(", ".join(strings))

        self.current_snapshot_id = None


from loguru import logger

with logger.catch():
    LikedSongsSyncer().debug_sync_playlist()
