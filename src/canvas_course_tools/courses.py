import rich_click as click
from rich import box, print
from rich.table import Table

from canvas_course_tools import configfile
from canvas_course_tools.canvas_tasks import (
    CanvasTasks,
    Forbidden,
    InvalidAccessToken,
    ResourceDoesNotExist,
)
from canvas_course_tools.utils import get_canvas


@click.group()
def courses():
    """Add, remove and list Canvas courses."""
    pass


@courses.command("list")
@click.argument("server_alias", type=str, default="")
@click.option(
    "-c",
    "--codes/--no-codes",
    "use_codes",
    help="Include course codes.",
    default=False,
)
def list_courses(server_alias, use_codes):
    """List Canvas courses.

    Without an argument, list all courses previously registered with an alias.
    When called with the SERVER_ALIAS argument, list all canvas courses
    available at that server.
    """
    config = configfile.read_config()
    if server_alias:
        canvas = get_canvas(server_alias)
        try:
            courses = canvas.list_courses()
        except InvalidAccessToken:
            raise click.UsageError(f"You must update your canvas access token.")
        else:
            aliases = {
                v["course_id"]: k
                for k, v in config.get("courses", {}).items()
                if v["server"] == server_alias
            }
            for course in courses:
                course.alias = aliases.get(course.id, None)
            print_courses(courses, use_codes)
    else:
        courses = []
        if "courses" in config:
            for alias, course in config["courses"].items():
                canvas = get_canvas(course["server"])
                course = canvas.get_course(course["course_id"])
                course.alias = alias
                courses.append(course)
            print_courses(courses, use_codes)
        else:
            raise click.UsageError("No courses are registered yet.")


@courses.command("add")
@click.argument("alias")
@click.argument("server_alias")
@click.argument("course_id", type=int)
@click.option(
    "-U",
    "--update",
    is_flag=True,
    help="If alias already exists, update to the new course.",
)
def add_course(alias, course_id, server_alias, update):
    """Register a course using an alias."""
    config = configfile.read_config()
    courses = config.setdefault("courses", {})
    if alias in courses and not update:
        print(f"[bold red] Course '{alias}' already exists.[/bold red]")
    else:
        try:
            server = config["servers"][server_alias]
        except KeyError:
            print(f"[bold red] Unknown server '{server_alias}'.[/bold red]")
        else:
            canvas = CanvasTasks(server["url"], server["token"])
            try:
                canvas.get_course(course_id)
            except ResourceDoesNotExist:
                print(f"[bold red]This course ID does not exist.[/bold red]")
            except Forbidden:
                print(
                    f"[bold red]You don't have authorization for this course.[/bold red]"
                )
            else:
                courses[alias] = {"server": server_alias, "course_id": course_id}
                configfile.write_config(config)


@courses.command("remove")
@click.argument("alias", type=str)
def remove_course(alias):
    """Remove course from configuration."""
    config = configfile.read_config()
    try:
        del config["courses"][alias]
    except KeyError:
        print(f"[bold red] Unknown course '{alias}'.[/bold red]")
    else:
        configfile.write_config(config)
        print(f"Course '{alias}' removed.")


def print_courses(courses, use_codes):
    """Print a list of courses in a formatted table.

    Args:
        courses (list): list of Canvas courses
        use_codes (bool): if True, show the SIS course code
    """
    table = Table(box=box.HORIZONTALS)
    table.add_column("ID")
    table.add_column("Alias")
    if use_codes:
        table.add_column("Course Code")
    table.add_column("Name")
    table.add_column("Term")
    for course in courses:
        fields = [str(course.id), course.alias, course.name, course.term]
        if use_codes:
            fields.insert(1, course.course_code)
        table.add_row(*fields)
    print()
    print(table)
