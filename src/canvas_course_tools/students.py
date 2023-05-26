import rich_click as click

from canvas_course_tools import configfile
from canvas_course_tools.utils import find_course, get_canvas


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
    canvas, course = find_course(course_alias)
    print(f"# {course.name}\n")
    if all:
        students = canvas.get_students(course.id)
        students.sort(key=lambda x: x.sortable_name)
        for student in students:
            print(f"{student.name} ({student.id})")
    else:
        for section in canvas.get_sections(course.id):
            print(f"## {section.name}\n")
            section.students.sort(key=lambda x: x.sortable_name)
            for student in section.students:
                print(f"{student.name} ({student.id})")
            print("\n")


@students.command("listgroups")
@click.argument("server_alias", type=str)
@click.argument("group_set_id", type=int)
def list_students_from_group_set(server_alias, group_set_id: int) -> None:
    """List all students in a group set.

    List all students who are part of group set GROUP_SET_ID on server
    SERVER_ALIAS. Group sets are stored as independent objects on a Canvas
    server. Retrieve group set IDs using the `canvas groups list` command. All
    groups which are part of the group set are returned along with their
    respective students.
    """
    canvas = get_canvas(server_alias)
    group_set = canvas.get_groupset(group_set_id)
    print(f"# {group_set.name}\n")
    for group in canvas.list_groups(group_set):
        print(f"## {group.name}\n")
        students = canvas.get_students_in_group(group)
        students.sort(key=lambda x: x.sortable_name)
        for student in students:
            print(f"{student.name} ({student.id})")
        print("\n")
