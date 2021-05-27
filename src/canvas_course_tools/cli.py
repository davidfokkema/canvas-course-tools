"""Canvas course tools command-line application.

This command-line application enables you to quickly perform a variety of tasks
that would otherwise require you to log in to a Canvas site. Since using this
tool requires no mouse-clicks at all, these tasks are performed much quicker and
easier than throug the web interface.
"""

import pathlib

import appdirs
import click
import dateutil.parser
from rich import print, box
from rich.table import Table
import toml

from canvas_course_tools.canvas_tasks import CanvasTasks

from . import __version__

APP_NAME = "canvas-course-tools"
CONFIG_FILE = "config.toml"


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@cli.group()
def servers():
    pass


@servers.command("list")
def show_servers():
    """List the registered servers."""
    config = read_config()
    try:
        servers = config["servers"]
    except KeyError:
        pass
    else:
        table = Table(box=None)
        table.add_column("Alias")
        table.add_column("URL")
        for alias, settings in servers.items():
            table.add_row(alias, settings["url"])
        print()
        print(table)


@servers.command("add")
@click.argument("alias", type=str)
@click.argument("url", type=str)
@click.argument("token", type=str)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="If alias already exists, force overwrite.",
)
def add_server(alias, url, token, force):
    """Register an alias for a server with corresponding access token.

    Example:

        canvas servers add school http://school.example.com/ 123~secret
    """
    config = read_config()
    servers = config.setdefault("servers", {})
    if alias in servers and not force:
        print(f"[bold red] Server alias {alias} already exists.[/bold red]")
    else:
        servers[alias] = {"url": url, "token": token}
        write_config(config)


@servers.command("remove")
@click.argument("alias", type=str)
def remove_server(alias):
    """Remove server from configuration."""
    config = read_config()
    try:
        del config["servers"][alias]
    except KeyError:
        print(f"[bold red] Unknown server alias {alias}.[/bold red]")
    else:
        write_config(config)
        print(f"Server alias {alias} removed.")


@cli.group()
def courses():
    pass


@courses.command("list")
@click.argument("alias", type=str)
def list_courses(alias):
    """List Canvas courses."""
    config = read_config()
    try:
        server = config["servers"][alias]
    except KeyError:
        print(f"[bold red] Unknown server alias {alias}.[/bold red]")
    else:
        canvas = CanvasTasks(server["url"], server["token"])
        courses = canvas.list_courses()
        table = Table(box=box.HORIZONTALS)
        table.add_column("ID")
        table.add_column("Course Code")
        table.add_column("Name")
        table.add_column("Year")
        for course in courses:
            if course.start_at is not None:
                academic_year = academic_year_from_time(course.start_at)
            else:
                academic_year = "Unknown"
            table.add_row(
                str(course.id), course.course_code, course.name, academic_year
            )
        print()
        print(table)


def read_config():
    """Read configuration file."""
    config_path = get_config_path()
    if config_path.is_file():
        with open(config_path) as f:
            return toml.load(f)
    else:
        return {}


def write_config(config):
    """Write configuration file.

    Args:
        config: a dictionary containing the configuration.
    """
    create_config_dir()
    config_path = get_config_path()
    with open(config_path, "w") as f:
        toml.dump(config, f)


def get_config_path():
    """Get path of configuration file."""
    config_dir = pathlib.Path(appdirs.user_config_dir(APP_NAME))
    config_path = config_dir / CONFIG_FILE
    return config_path


def create_config_dir():
    """Create configuration directory if necessary."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)


def academic_year_from_time(time):
    """Return the academic year from a time string.

    Args:
        time: a string with a time in ISO format.
    """
    time = dateutil.parser.isoparse(time)
    start_year = time.year
    if time.month < 8:
        start_year -= 1
    return f"{start_year}-{start_year + 1}"