"""Display upto 50 recently played tracks."""
from datetime import datetime

from rich.table import Table

from spotils import console, instance
from spotils.helpers.time import time_since

GREY = "grey50"


def print_recently_played_tracks(limit: int = 50) -> None:
    """Display the recently played tracks (upto limit) in a table."""
    table = Table(
        title="Recently played tracks",
        caption="Recent -> Older",
        show_lines=True,
        show_edge=False,
    )
    table.add_column("DATE PLAYED", style=GREY)
    table.add_column("TITLE")
    table.add_column("ALBUM", style=GREY)
    table.add_column()  # Liked
    table.add_column(style=GREY)  # Duration

    # TODO: Handle the case when played_items is empty
    played_items = instance.current_user_recently_played(limit).items
    track_ids = [played_item.track.id for played_item in played_items]

    saved_statuses = instance.current_user_saved_tracks_contains(track_ids)

    for played_item, is_saved in zip(played_items, saved_statuses):
        iso_time = played_item.played_at.removesuffix("Z")
        played_at = datetime.fromisoformat(iso_time)
        track = played_item.track
        emoji = "\N{GREEN HEART}" if is_saved else "\N{WHITE HEART}"
        artists = ", ".join(artist.name for artist in track.artists)

        table.add_row(
            time_since(played_at, max_units=1),
            f"[bold]{track.name}[/]\n[{GREY}]{artists}[/]",
            track.album.name,
            emoji,
            track.formatted_duration(),
        )

    console.print(table)
