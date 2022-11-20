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


def run_tasks() -> None:
    """
    Run the tasks specified by the config.

    It blocks the current thread until all tasks finish.
    """
    task_threads = []

    if config.LikedSongsSync.enabled:
        syncer = LikedSongsSyncer()
        if config.LikedSongsSync.short_sync_enabled:
            thread = schedule_task(
                "Liked Songs Syncer (short)",
                config.LikedSongsSync.short_sync_interval,
                syncer.sync_playlist,
                config.LikedSongsSync.short_sync_limit,
            )
            task_threads.append(thread)

        thread = schedule_task(
            "Liked Songs Syncer (full)",
            config.LikedSongsSync.full_sync_interval,
            syncer.sync_playlist,
        )
        task_threads.append(thread)

    if config.SkipLikedSongs.enabled:
        thread = schedule_task(
            "Liked Songs Skipper",
            config.SkipLikedSongs.interval,
            skip_if_liked,
        )
        task_threads.append(thread)

    event = threading.Event()
    # Sleep the main thread until all tasks finish.
    event.wait()
