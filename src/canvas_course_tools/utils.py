import click

from canvas_course_tools import configfile
from canvas_course_tools.canvas_tasks import CanvasTasks


def get_canvas(server_alias):
    config = configfile.read_config()
    try:
        server = config["servers"][server_alias]
    except KeyError:
        raise click.UsageError(f"Unknown server '{server_alias}'.")
    else:
        return CanvasTasks(server["url"], server["token"])
