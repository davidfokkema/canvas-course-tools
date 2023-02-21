import re

from canvas_course_tools.datatypes import GroupList, Student, StudentGroup

PARSE_STUDENT_RE = re.compile("(?P<name>.*) \((?P<id>.*)\) *(?:\[(?P<notes>.*)\])?")


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
