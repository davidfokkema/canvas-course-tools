"""Canvas course tools command-line application.

This command-line application enables you to quickly perform a variety of tasks
that would otherwise require you to log in to a Canvas site. Since using this
tool requires no mouse-clicks at all, these tasks are performed much quicker and
easier than through the web interface.
"""

import rich_click as click
import trogon

from canvas_course_tools import __version__
from canvas_course_tools.courses import courses
from canvas_course_tools.groups import groups
from canvas_course_tools.servers import servers
from canvas_course_tools.students import students
from canvas_course_tools.templates import templates


@trogon.tui()
@click.group()
@click.version_option(version=__version__)
def cli():
    pass


cli.add_command(servers)
cli.add_command(courses)
cli.add_command(students)
cli.add_command(templates)
cli.add_command(groups)


if __name__ == "__main__":
    cli()
