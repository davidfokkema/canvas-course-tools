import rich_click as click

from canvas_course_tools import configfile
from canvas_course_tools.utils import get_canvas


@click.group()
def students():
    """Search for or list students."""
    pass


@students.command("list")
@click.argument("course_alias")
@click.option(
    "--all/-no-all",
    default=False,
    help="List all students without splitting them into sections.",
)
def list_students(course_alias, all):
    """List students in course COURSE_ALIAS.

    Students are split into sections by default.
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
    print(f"# {course.name}\n")
    if all:
        students = canvas.get_students(course_id)
        students.sort(key=lambda x: x.sortable_name)
        for student in students:
            print(f"{student.name} ({student.id})")
    else:
        for section in canvas.get_sections(course_id):
            print(f"## {section.name}\n")
            section.students.sort(key=lambda x: x.sortable_name)
            for student in section.students:
                print(f"{student.name} ({student.id})")
            print("\n")
