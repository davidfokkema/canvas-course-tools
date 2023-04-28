import importlib.resources
import pathlib

import jinja2
import rich_click as click
import tomli
from rich import box
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from canvas_course_tools.datatypes import GroupList
from canvas_course_tools.group_lists import parse_group_list

TEMPLATE_INFO_FILE = "template-info.toml"


@click.group()
def templates():
    """Generate files based on templates and group lists."""
    pass


@templates.command("list")
def list_templates():
    """List all available templates."""
    template_files = importlib.resources.files("canvas_course_tools") / "templates"
    info_file = template_files / TEMPLATE_INFO_FILE
    info = tomli.loads(info_file.read_text(encoding="utf-8"))

    table = Table(box=box.HORIZONTALS)
    table.add_column("Template")
    table.add_column("Description")
    for template in sorted(template_files.iterdir()):
        if template.is_file() and not template == info_file:
            table.add_row(template.name, info.get(template.name, ""))
    console = Console()
    console.print()
    console.print(table)


@templates.command("show")
@click.argument("template")
def show_template(template):
    """Show the contents of a template.

    The argument, TEMPLATE, should be the name of one of the templates
    registered with the app. Use the `list` command to get a list of templates.
    """
    template_files = importlib.resources.files("canvas_course_tools") / "templates"
    path = template_files / template
    console = Console()

    if not path.is_file():
        raise click.BadArgumentUsage(f"Template {template} not found!")
    elif console.is_terminal:
        syntax = Syntax.from_path(path)
        console.print()
        console.print(syntax)
    else:
        print(path.read_text(encoding="utf-8"))


@templates.command()
@click.argument("template")
@click.argument("group_list")
@click.option(
    "-f",
    "--file",
    help="Write the output to this file.",
)
@click.option(
    "-w",
    "--write",
    "auto_write",
    is_flag=True,
    help="Write the output to file based on template and group list names. This option has no effect when --file is also used.",
)
@click.option(
    "-d",
    "--dir",
    "output_dir",
    help="Write output to a file relative to this directory.",
)
@click.option(
    "-p",
    "--photos",
    "photo_dir",
    type=click.Path(
        file_okay=False, dir_okay=True, exists=True, path_type=pathlib.Path
    ),
    help="Search matching photos in this directory.",
)
def render(template, group_list, file, auto_write, output_dir, photo_dir):
    """Render a template.

    The first argument, TEMPLATE, should be the name of one of the templates
    registered with the app or a path of a template file. Use the `list` command
    to get a list of included templates.

    The second argument, GROUP_LIST, should be a path to a group list file. If a
    line starts with a #-character, the rest of the line is interpreted as a
    title. If it starts with ##, the rest of the line is interpreted as a group
    name. There can be multiple groups defined in one file. All other non-empty
    lines are interpreted as a student name with optional student id and notes
    field. It must be of the form "student name (id) [notes]". For example, the
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

    If the --photos option is given on the command line, for each student a
    matching photo is looked up in this directory. The name of the file should
    match the full name of the student *exactly*. E.g. "Drew Ferrel.jpg" for the
    first student in the example group list file. The extension does not matter
    and is passed as is to the template.

    \f
    Ignore the \b and \f characters in this docstring. They are to tell click to
    not wrap paragraphs (\b) and not display this note (\f).
    """
    file_contents = pathlib.Path(group_list).read_text(encoding="utf-8")

    if file or auto_write:
        output_path = build_output_path(file, output_dir, template, group_list)
        relative_to = output_path.parent
    else:
        relative_to = None

    group_list_data = parse_group_list(
        file_contents, photo_dir, relative_to=relative_to
    )
    contents = render_template(template, group_list_data)

    if not file and not auto_write:
        # output to console
        console = Console()
        if console.is_terminal:
            filetype = pathlib.Path(template).suffix.lstrip(".")
            syntax = Syntax(contents, lexer=filetype)
            console.print()
            console.print(syntax)
        else:
            print(contents)
    else:
        print(f"Writing template output to {output_path}...")
        try:
            output_path.write_text(contents, encoding="utf-8")
        except FileNotFoundError:
            raise click.BadArgumentUsage(
                f"Output file {output_path} cannot be created."
            )


def build_output_path(file, output_dir, template, group_list):
    """Build output path based on various options and arguments.

    If file is given, this will be the filename. Else a filename will be
    generated by concatenating the template name and the group_list name. The
    returned path is the filename relative to the output_dir directory.

    Args:
        file (str): the filename
        output_dir (str): the output directory
        template (str): the name of the template file
        group_list (str): the name of the group list file

    Returns:
        pathlib.Path: the generated output path
    """
    if output_dir:
        output_dir = pathlib.Path(output_dir)
    else:
        output_dir = pathlib.Path()

    if file:
        path = output_dir / file
    else:
        template_path = pathlib.Path(template)
        filename = template_path.stem + "-" + pathlib.Path(group_list).stem
        filepath = pathlib.Path(filename).with_suffix(template_path.suffix)
        path = output_dir / filepath
    return path


def render_template(template_name, group_list: GroupList):
    """Render a template.

    Args:
        template_name (str): the name of the template or a path to a template
            file.
        group_list (GroupList): the group list as input for the template
    """
    if pathlib.Path(template_name).is_file():
        env = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
    else:
        env = jinja2.Environment(
            loader=jinja2.PackageLoader("canvas_course_tools", "templates"),
        )
    try:
        template = env.get_template(template_name, globals={"zip": zip})
    except jinja2.exceptions.TemplateNotFound:
        raise click.BadArgumentUsage(f"Template {template_name} not found!")
    return template.render(title=group_list.name, groups=group_list.groups)
