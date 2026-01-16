import click

from canvas_course_tools import configfile
from canvas_course_tools.canvas_tasks import (
    CanvasForbidden,
    CanvasResourceDoesNotExist,
    CanvasTasks,
    Course,
)


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
    try:
        course = canvas.get_course(course_id)
    except CanvasResourceDoesNotExist:
        raise click.UsageError(f"Course {course_alias} does not exist on the server.")
    except CanvasForbidden:
        raise click.UsageError(
            f"You don't have authorization to access course {course_alias}."
        )
    return canvas, course
