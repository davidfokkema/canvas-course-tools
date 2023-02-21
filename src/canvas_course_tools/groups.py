import pathlib
import itertools
import re
from pathlib import Path

import click

from canvas_course_tools import configfile
from canvas_course_tools.utils import get_canvas
from canvas_course_tools.group_lists import parse_group_list
from canvas_course_tools.canvas_tasks import CanvasObjectExistsError


@click.group()
def groups():
    """Create Canvas groups based on group lists."""
    pass


@groups.command("create")
@click.argument("course_alias")
@click.argument("group_list")
@click.option(
    "--groupset", "groupset_name", required=True, help="Name of the groupset to create."
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Whether or not to overwrite an existing groupset.",
)
def create_canvas_groups(course_alias, group_list, groupset_name, overwrite):
    """Create canvas groups."""
    config = configfile.read_config()
    server, course_id = (
        config["courses"][course_alias][k] for k in ("server", "course_id")
    )
    canvas = get_canvas(server)
    course = canvas.get_course(course_id)

    file_contents = pathlib.Path(group_list).read_text()
    group_list = parse_group_list(file_contents)

    try:
        groupset = canvas.create_groupset(groupset_name, course, overwrite)
    except CanvasObjectExistsError:
        raise click.BadArgumentUsage(f"Canvas groupset {groupset_name} already exists.")

    for group in group_list.groups:
        canvas_group = canvas.create_group(group.name, groupset)
        for student in group.students:
            canvas.add_student_to_group(student, canvas_group)
