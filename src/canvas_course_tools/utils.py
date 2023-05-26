import click

from canvas_course_tools import configfile
from canvas_course_tools.canvas_tasks import CanvasTasks, Course


def get_canvas(server_alias):
    config = configfile.read_config()
    try:
        server = config["servers"][server_alias]
    except KeyError:
        raise click.UsageError(f"Unknown server '{server_alias}'.")
    else:
        return CanvasTasks(server["url"], server["token"])


def find_course(course_alias: str) -> tuple[CanvasTasks, Course]:
    config = configfile.read_config()
    try:
        server, course_id = (
            config["courses"][course_alias][k] for k in ("server", "course_id")
        )
    except KeyError:
        raise click.BadArgumentUsage(f"Unknown course {course_alias}.")
    canvas = get_canvas(server)
    course = canvas.get_course(course_id)
    return canvas, course
