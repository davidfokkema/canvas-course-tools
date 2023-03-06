import pathlib

import rich_click as click
from rich import print
from rich.progress import Progress

from canvas_course_tools import configfile
from canvas_course_tools.canvas_tasks import (
    CanvasObjectExistsError,
    Forbidden,
    ResourceDoesNotExist,
)
from canvas_course_tools.group_lists import parse_group_list
from canvas_course_tools.utils import get_canvas


@click.group()
def groups():
    """Create Canvas groups based on group lists."""
    pass


@groups.command("create")
@click.argument("course_alias")
@click.argument("group_list")
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Whether or not to overwrite an existing groupset.",
)
def create_canvas_groups(course_alias, group_list, overwrite):
    """Create canvas groups.

    Create canvas groups in course COURSE_ALIAS based on the group list defined
    in GROUP_LIST. The groups will be placed in GroupSet named after the title
    in the group list file.

    The GROUP_LIST argument should be a path to a group list file. If a line
    starts with a #-character, the rest of the line is interpreted as a title.
    If it starts with ##, the rest of the line is interpreted as a group name.
    There can be multiple groups defined in one file. All other non-empty lines
    are interpreted as a student name with optional student id and notes field.
    It must be of the form "student name (id) [notes]". For example, the
    following is a valid group list file:

        \b
        # Physics 101
        ## Group A
        Drew Ferrell (800057) [second year]
        Amanda James (379044)
        Antonio Morris (804407) [skips thursdays]

        \b
        ## Group B
        Elizabeth Allison (312702)
        James Morales (379332)

    \f
    Ignore the \b and \f characters in this docstring. They are to tell click to
    not wrap paragraphs (\b) and not display this note (\f).
    """
    config = configfile.read_config()
    try:
        server, course_id = (
            config["courses"][course_alias][k] for k in ("server", "course_id")
        )
    except KeyError:
        raise click.BadArgumentUsage(f"Unknown course {course_alias}.")
    canvas = get_canvas(server)
    course = canvas.get_course(course_id)

    file_contents = pathlib.Path(group_list).read_text()
    group_list = parse_group_list(file_contents)

    print(f"Creating GroupSet {group_list.name}...")
    try:
        groupset = canvas.create_groupset(group_list.name, course, overwrite)
    except CanvasObjectExistsError:
        raise click.BadArgumentUsage(
            f"Canvas groupset '{group_list.name}' already exists. You can use --overwrite."
        )

    with Progress() as progress:
        task_groups = progress.add_task(
            description="Creating groups...", total=len(group_list.groups)
        )
        task_students = progress.add_task(description="Adding students to group...")

        for group in group_list.groups:
            canvas_group = canvas.create_group(group.name, groupset)
            progress.reset(task_students, total=len(group.students))
            for student in group.students:
                try:
                    canvas.add_student_to_group(student, canvas_group)
                except ResourceDoesNotExist:
                    print(f"[red]WARNING: student {student.name} does not exist.")
                except Forbidden:
                    print(
                        f"[red]WARNING: you do not have authorization to add student {student.name}."
                    )
                progress.advance(task_students)
            progress.advance(task_groups)
            print(f"Created {group.name}.")

    print("Done")
