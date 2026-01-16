"""Canvas course tools command-line application.

This command-line application enables you to quickly perform a variety of tasks
that would otherwise require you to log in to a Canvas site. Since using this
tool requires no mouse-clicks at all, these tasks are performed much quicker and
easier than through the web interface.
"""

import sys

import rich_click as click
import trogon
from rich import print

from canvas_course_tools import __version__
from canvas_course_tools.canvas_tasks import (
    CanvasAPIError,
    CanvasForbidden,
    CanvasInvalidAccessToken,
    CanvasObjectExistsError,
    CanvasResourceDoesNotExist,
    IncorrectURL,
)
from canvas_course_tools.courses import courses
from canvas_course_tools.groups import groups
from canvas_course_tools.servers import servers
from canvas_course_tools.students import students
from canvas_course_tools.templates import templates


class CanvasGroup(click.Group):
    """Custom Click group that handles Canvas exceptions gracefully."""

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except IncorrectURL as e:
            print(f"[bold red]Connection Error:[/bold red] {e}", file=sys.stderr)
            ctx.exit(1)
        except CanvasInvalidAccessToken as e:
            print(
                f"[bold red]Authentication Error:[/bold red] Invalid access token. Please update your credentials.",
                file=sys.stderr,
            )
            ctx.exit(1)
        except CanvasForbidden as e:
            print(
                f"[bold red]Authorization Error:[/bold red] You don't have permission to access this resource.",
                file=sys.stderr,
            )
            ctx.exit(1)
        except CanvasResourceDoesNotExist as e:
            print(
                f"[bold red]Not Found:[/bold red] The requested resource does not exist.",
                file=sys.stderr,
            )
            ctx.exit(1)
        except CanvasObjectExistsError as e:
            print(
                f"[bold red]Already Exists:[/bold red] {e}",
                file=sys.stderr,
            )
            ctx.exit(1)
        except CanvasAPIError as e:
            print(f"[bold red]Canvas API Error:[/bold red] {e}", file=sys.stderr)
            ctx.exit(1)


@trogon.tui()
@click.group(cls=CanvasGroup)
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
