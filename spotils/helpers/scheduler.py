"""A scheduler for running tasks between interval."""
import threading
import time
import typing as t

from schedule import Scheduler

from spotils import config
from spotils.helpers.time import parse_interval
from spotils.utils.liked_songs_sync import LikedSongsSyncer
from spotils.utils.skip_liked import skip_if_liked


def loop_task(
    interval: str, callback: t.Callable[..., object], *args: t.Any
) -> t.NoReturn:
    """
    Create a new scheduler for running a task, and block.

    interval: The interval (seconds) to run the task at.
    function: The callback to run.
    args: The arguments to pass to the callback.

    This should be run inside a different thread as it blocks the
    current thread to run the pending tasks of the new scheduler.
    """
    scheduler = Scheduler()
    seconds = parse_interval(interval)
    scheduler.every(seconds).seconds.do(callback, *args)
    scheduler.run_all()

    while True:
        scheduler.run_pending()
        time.sleep(1)


def schedule_task(
    name: str, interval: str, callback: t.Callable[..., object], *args: t.Any
) -> threading.Thread:
    """
    Schedule a task to be run inside a new thread.

    interval: The interval (seconds) to run the task at.
    function: The callback to run.
    args: The arguments to pass to the callback.

    The created thread is returned.
    """
    thread = threading.Thread(
        target=loop_task,
        name=name,
        args=(interval, callback, *args),
        daemon=True,
    )
    thread.start()
    return thread


class LikedSongsSyncTick:
    """
    Manage full syncs and short syncs properly.

    Short syncs shouldn't be run close to full syncs and if their
    intervals coincidence, only the full sync should be run. To achieve
    this behaviour, syncs run at "ticks".
    """

    def __init__(self) -> None:
        self.syncer = LikedSongsSyncer()
        self.required_long_ticks = self.get_required_long_ticks()
        self.long_tick = self.required_long_ticks

    @staticmethod
    def get_required_long_ticks() -> int:
        """
        Calculate the number of ticks for the full sync interval.

        The full sync interval is adjusted (rounded to the nearest)
        to a multiple of the short sync interval. This is done so its
        interval can be expressed as a tick.
        """
        short_seconds = parse_interval(
            config.LikedSongsSync.short_sync_interval
        )
        long_seconds = parse_interval(config.LikedSongsSync.full_sync_interval)

        required_decrement = long_seconds % short_seconds

        lowest_multiple = long_seconds // short_seconds
        upper_interval = lowest_multiple + short_seconds
        required_increment = upper_interval - long_seconds

        if required_decrement > required_decrement:
            long_seconds += required_increment
        else:
            long_seconds -= required_decrement
        return long_seconds // short_seconds

    def handle_tick(self) -> None:
        """
        Handle what happens at a tick.

        If the long tick limit is reached, a full sync is run.
        Otherwise, a short sync is run.
        """
        if self.long_tick == self.required_long_ticks:
            self.syncer.sync_playlist()
            self.long_tick = 1
            return

        self.syncer.sync_playlist(limit=config.LikedSongsSync.short_sync_limit)
        self.long_tick += 1


def run_tasks() -> None:
    """
    Run the tasks specified by the config.

    Block the current thread indefinitely.
    """
    if config.LikedSongsSync.enabled:
        if config.LikedSongsSync.short_sync_enabled:
            tick_syncer = LikedSongsSyncTick()

            schedule_task(
                "Liked Songs Syncer",
                config.LikedSongsSync.short_sync_interval,
                tick_syncer.handle_tick,
            )
        else:
            syncer = LikedSongsSyncer()
            schedule_task(
                "Liked Songs Syncer (full)",
                config.LikedSongsSync.full_sync_interval,
                syncer.sync_playlist,
            )

    if config.SkipLikedSongs.enabled:
        schedule_task(
            "Liked Songs Skipper",
            config.SkipLikedSongs.interval,
            skip_if_liked,
        )

    event = threading.Event()
    # Sleep the main thread until all tasks finish.
    event.wait()
