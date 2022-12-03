"""Defines the CLI interface."""
import typing as t

import click
from click.shell_completion import CompletionItem
from rich.pretty import Pretty

from spotils import console
from spotils.config import (
    config_data,
    default_config_data,
    local_config_data,
    set_config_value,
    unset_config_key,
)
from spotils.helpers.nested_key_mapping import ConfigMapping
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
    ctx: click.Context, param: click.Parameter, value: str
) -> JSONVals:
    """
    Parse the user's value according to the provided key.

    For example, if the key holds a boolean, then 1, yes, etc are
    acceptable, according to Click's converting scheme.
    Returns the converted value.
    """
    key = ctx.params["key"]
    target_type = type(default_config_data[key])
    converter = click.types.convert_type(target_type)
    value = converter.convert(value, param, ctx)
    return value


def complete_keys(
    ctx: click.Context, args: t.List[str], incomplete: str
) -> list[CompletionItem]:
    """Complete the key typed so far."""
    to_parse: list[tuple[str, t.Mapping]] = [("", default_config_data)]
    available_keys: list[str] = []

    while to_parse:
        current = to_parse.pop()
        parent_key, value = current

        if not isinstance(value, t.Mapping):
            available_keys.append(parent_key)
            continue

        for subkey, subvalue in value.items():
            new_key = f"{parent_key}.{subkey}" if parent_key else subkey

            if isinstance(subvalue, t.Mapping):
                to_parse.append((new_key, subvalue))
            else:
                available_keys.append(new_key)

    return [
        CompletionItem(key)
        for key in available_keys
        if key.startswith(incomplete)
    ]


@app.group()
def config() -> None:
    """Change/Read the application's config."""


key_argument = click.argument(
    "key",
    type=str,
    callback=validate_config_key,
    shell_complete=complete_keys,
)


def pretty_print(mapping: ConfigMapping) -> None:
    """Pretty print a config mapping with rich."""
    # We need to pass the internal dict to get the desired output.
    console.print(Pretty(mapping.data, expand_all=True))


def print_config(
    ctx: click.Context, param: click.Parameter, value: str
) -> None:
    """Print the current config."""
    if not value or ctx.resilient_parsing:
        return
    pretty_print(default_config_data)
    ctx.exit()


def print_overriden_config(
    ctx: click.Context, param: click.Parameter, value: str
) -> None:
    """Print the default config."""
    if not value or ctx.resilient_parsing:
        return
    pretty_print(local_config_data)
    ctx.exit()


@config.command()
@key_argument
@click.option(
    "--all",
    is_flag=True,
    callback=print_config,
    expose_value=False,
    is_eager=True,
)
@click.option(
    "--local",
    is_flag=True,
    callback=print_overriden_config,
    expose_value=False,
    is_eager=True,
)
def get(key: str) -> None:
    """
    Get the value of a config option.

    Example: spotils config get spotify.liked_songs_playlist_id
    """
    console.print(config_data[key])


@config.command()
@key_argument
@click.argument(
    "value",
    callback=parse_config_value,
)
def set(key: str, value: JSONVals) -> None:
    """
    Set the value of a config key.

    Example: spotils config set spotify.liked_songs_playlist_id 50xy7...
    """
    set_config_value(key, value)


@config.command()
@key_argument
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
