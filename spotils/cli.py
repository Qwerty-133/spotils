"""Defines the CLI interface."""
import click

from spotils.helpers.scheduler import run_tasks
from spotils.utils.recently_played import print_recently_played_tracks


@click.group(
    no_args_is_help=True,
    epilog="Run 'spotils command --help' to get help on a particular command.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.version_option(None, "-v", "--version", package_name=__package__)
def app() -> None:
    """A collection of different spotify utilities."""


@app.command()
@click.option(
    "-l",
    "--limit",
    help="Max number of results.",
    default=50,
    type=click.IntRange(min=1, max=50),
)
def recent(limit: int) -> None:
    """Display recently streamed tracks."""
    print_recently_played_tracks(limit)


@app.command()
def run() -> None:
    """Run all the enabled tasks."""
    run_tasks()
