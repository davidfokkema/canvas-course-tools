import pathlib

import appdirs
import click
from rich import print
import toml

from . import __version__

APP_NAME = "amsphyslab-course-tools"
APP_AUTHOR = "amsphyslab"
CONFIG_FILE = "config.toml"


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@cli.group()
def apikey():
    pass


@apikey.command("show")
def show_apikey():
    """Show the registered API key."""
    config = read_config()
    try:
        key = config["canvas"]["apikey"]
    except KeyError:
        print("[bold red]ERROR: API key not yet defined.[/bold red]")
        print()
        print("Use [green]canvas apikey set[/green]")
    else:
        print(f"API key: {key}")


def read_config():
    """Read configuration file."""
    config_dir = pathlib.Path(appdirs.user_config_dir(APP_NAME, APP_AUTHOR))
    config_path = config_dir / CONFIG_FILE
    if config_path.is_file():
        with open(config_path) as f:
            return toml.load(f)
    else:
        return {}