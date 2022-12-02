"""Defines the CLI interface."""
import typing as t

import click

from spotils import console
from spotils.config import (
    config_data,
    default_config_data,
    local_config_data,
    set_config_value,
    unset_config_key,
)
from spotils.helpers.scheduler import run_tasks
from spotils.type_aliases import JSONVals
from spotils.utils.recently_played import print_recently_played_tracks


@click.group(
    no_args_is_help=True,
    epilog="Run 'spotils command --help' to get help on a particular command.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.version_option(None, "-v", "--version", package_name=__package__)
def app() -> None:
    """A collection of different spotify utilities."""


KeyPath: t.TypeAlias = tuple[str, str, str]


def validate_config_key(
    ctx: click.Context,
    param: click.Parameter,
    key: str,
) -> str:
    """Validate that the given key exists in the default config."""
    if key in default_config_data:
        return key

    raise click.BadParameter(f"'{key}' is not a valid config key.")


def validate_local_config_key(
    ctx: click.Context, param: click.Parameter, key: str
) -> str:
    """Validate that the given key exists in the local config."""
    # We need to ensure it's a valid key first.
    validate_config_key(ctx, param, key)
    if key in local_config_data:
        return key

    raise click.BadParameter(f"'{key}' has not been set yet.")


def parse_config_value(
    ctx: click.Context, param: click.Parameter, kv: tuple[str, str]
) -> tuple[str, JSONVals]:
    """
    Parse a JSON value according to the provided key.

    The key must also belong in the default config.
    The return value is a tuple containing the key and the (converted)
    value.
    """
    validate_config_key(ctx, param, kv[0])
    target_type = type(default_config_data[kv[0]])
    converter = click.types.convert_type(target_type)
    value = converter.convert(kv[1], param, ctx)
    return (kv[0], value)


@app.group()
def config() -> None:
    """Change/Read the application's config."""


@config.command()
@click.argument(
    "key",
    type=str,
    callback=validate_config_key,
)
def get(key: str) -> None:
    """
    Get the value of a config option.

    Example: spotils config get spotify.liked_songs_playlist_id
    """
    console.print(config_data[key])


@config.command()
@click.argument(
    "key_and_value",
    nargs=2,
    callback=parse_config_value,
)
def set(key_and_value: tuple[str, JSONVals]) -> None:
    """
    Set the value of a config key.

    Example: spotils config set spotify.liked_songs_playlist_id 50xy7...
    """
    set_config_value(*key_and_value)


@config.command()
@click.argument(
    "key",
    callback=validate_local_config_key,
)
def unset(key: str) -> None:
    """
    Unset a config value.

    Example: spotils config unset spotify.liked_songs_playlist_id
    """
    unset_config_key(key)


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
