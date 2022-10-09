"""Canvas course tools command-line application.

This command-line application enables you to quickly perform a variety of tasks
that would otherwise require you to log in to a Canvas site. Since using this
tool requires no mouse-clicks at all, these tasks are performed much quicker and
easier than throug the web interface.
"""

import rich_click as click

from canvas_course_tools import __version__
from canvas_course_tools.courses import courses
from canvas_course_tools.servers import servers
from canvas_course_tools.students import students


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


cli.add_command(servers)
cli.add_command(courses)
cli.add_command(students)


if __name__ == "__main__":
    cli()
