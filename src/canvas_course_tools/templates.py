import importlib.resources
import pathlib
import re

import click
import jinja2

from canvas_course_tools.datatypes import GroupList, Student, StudentGroup

PARSE_STUDENT_RE = re.compile("(?P<name>.*) \((?P<id>.*)\) *(?:\[(?P<notes>.*)\])?")


@click.group()
def templates():
    """Generate files based on templates and group lists."""
    pass


@templates.command("render")
@click.argument("template")
@click.argument("group_list")
def render_template(template, group_list):
    """Render a template.

    The first argument, TEMPLATE, should be the name of one of the templates
    registered with the app. Use the `list` command to get a list of templates.

    The second argument, GROUP_LIST, should be a path to a group list file. If a
    file starts with a #-character, the rest of the line is interpreted as a
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

    \f
    Ignore the \b and \f characters in this docstring. They are to tell click to
    not wrap paragraphs (\b) and not display this note (\f).
    """
    file_contents = pathlib.Path(group_list).read_text()
    group_list = parse_group_list(file_contents)
    contents = render_template(template, group_list)
    click.echo(contents)


def parse_group_list(text):
    """Parse text and build a group list."""
    group_list = GroupList()
    current_group = StudentGroup()

    for line in text.splitlines():
        if not line:
            # empty line
            continue
        elif line.startswith("##"):
            # new group name
            group_name = line.removeprefix("##").strip()
            if current_group.students:
                # there are students in the current group, add them to the list
                group_list.groups.append(current_group)
            # create new group
            current_group = StudentGroup(name=group_name)
        elif line.startswith("#"):
            # group list name
            group_list.name = line.removeprefix("#").strip()
        else:
            # must be a student
            match = PARSE_STUDENT_RE.match(line)
            if match:
                current_group.students.append(
                    Student(name=match["name"], id=match["id"], notes=match["notes"])
                )
    group_list.groups.append(current_group)

    return group_list


def render_template(template_name, group_list: GroupList):
    """Render a template.

    Args:
        template_name (str): the name of the template
        group_list (GroupList): the group list as input for the template
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader("canvas_course_tools", "templates")
    )
    try:
        template = env.get_template(template_name)
    except jinja2.exceptions.TemplateNotFound:
        raise click.BadArgumentUsage(f"Template {template_name} not found!")
    return template.render(title=group_list.name, groups=group_list.groups)
