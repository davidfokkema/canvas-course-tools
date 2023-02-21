import itertools
import re
from pathlib import Path

import canvasapi
import click


@click.command()
@click.argument("url")
@click.option(
    "--api_key",
    envvar="CANVAS_KEY",
    prompt="Please enter your Canvas API key",
    hide_input=True,
    help="Canvas Access Token (API key).",
)
@click.argument("input_path")
@click.option("--groupset", required=True, help="Name of the groupset to create.")
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Whether or not to overwrite an existing groupset.",
)
def create_canvas_groups(url, api_key, input_path, groupset, overwrite):
    """Create canvas groups."""
    course = get_canvas_course(url, api_key)
    if course:
        groups = read_groups_from_file(input_path)
        users = course.get_users()
        if groups:
            groupset = create_groupset(groupset, course, overwrite)
            for idx, student_ids in enumerate(itertools.zip_longest(*groups), start=1):
                group_name = f"Groep {idx}"
                group = groupset.create_group(name=group_name)
                for student_id in student_ids:
                    if student_id is not None:
                        try:
                            (user,) = [u for u in users if u.sis_user_id == student_id]
                        except ValueError:
                            click.secho(
                                f"Warning: student_id {student_id} not found.",
                                fg="red",
                                bold=True,
                            )
                        else:
                            group.create_membership(user)


def create_groupset(name, course, overwrite):
    """Create groupset in course.

    Args:
        name (string): name of the groupset
        course (canvasapi.course.Course): the course in which to create the groupset
        overwrite (bool): whether or not to overwrite an existing groupset

    Returns:
        canvasapi.group.GroupCategory: the newly created groupset
    """
    all_groupsets = list(course.get_group_categories())
    all_groupset_names = [g.name for g in all_groupsets]
    if name in all_groupset_names:
        if not overwrite:
            raise click.ClickException("Groupset already exists.")
        else:
            (groupset,) = [g for g in all_groupsets if g.name == name]
            groupset.delete()
    return course.create_group_category(name)


def get_canvas_course(url, api_key):
    """Get canvas course from URL and API key.

    Args:
        url (string): the canvas course web url
        api_key (string): the user's canvas API key
    """
    try:
        canvas_url, course_id = re.match("(https?://.*)/courses/([0-9]+)", url).groups()
    except AttributeError:
        click.secho(
            f"The URL {url} does not match a course url. Is the course_id included?",
            fg="red",
            bold=True,
        )
        return

    canvas = canvasapi.Canvas(canvas_url, api_key)
    return canvas.get_course(course_id)


def read_groups_from_file(input_path):
    """Read groups from file.

    Args:
        input_path (string): the path to the input file.
    """
    if not Path(input_path).is_file():
        click.secho(f"File {input_path} does not exist, skipping.", fg="red", bold=True)
    else:
        groups = []
        with open(input_path, "r") as f:
            current_group = []
            for line in f.readlines():
                if re.match("^#", line):
                    if current_group:
                        groups.append(current_group)
                    current_group = []
                elif m := re.match("^[^#].* \((\d+)\)", line):
                    current_group.append(m.group(1))
            if current_group:
                groups.append(current_group)
        return groups
