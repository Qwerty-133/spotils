"""Defines the CLI interface."""
import typer

from spotils.helpers.scheduler import run_tasks
from spotils.utils.recently_played import print_recently_played_tracks

app = typer.Typer(
    no_args_is_help=True, help="A collection of different spotify utilities."
)

recent_limit_option = typer.Option(
    50, "--limit", "-l", help="Max number of results", min=1, max=50
)


@app.command()
def recent(limit: int = recent_limit_option) -> None:
    """Display recently streamed tracks."""
    print_recently_played_tracks(limit)


@app.command()
def run() -> None:
    """Run all scheduled tasks."""
    run_tasks()


playlist_option = typer.Option(
    None, "--playlist", "-p", help="The target playlist."
)
