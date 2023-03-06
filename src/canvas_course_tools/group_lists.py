import itertools
import os.path
import pathlib
import re
import unicodedata

from rich.console import Console

from canvas_course_tools.datatypes import GroupList, Student, StudentGroup

PARSE_STUDENT_RE = re.compile("(?P<name>.*) \((?P<id>.*)\) *(?:\[(?P<notes>.*)\])?")


def parse_group_list(text, photo_dir=None, relative_to=None):
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
                if photo_dir:
                    photo = find_photo(match["name"], photo_dir)
                    if photo and relative_to is not None:
                        photo = pathlib.Path(os.path.relpath(photo, start=relative_to))
                else:
                    photo = None
                current_group.students.append(
                    Student(
                        name=match["name"],
                        id=match["id"],
                        notes=match["notes"],
                        photo=photo,
                    ),
                )
    group_list.groups.append(current_group)

    return group_list


def find_photo(name, photo_dir):
    """Find a photo for a given student name.

    Args:
        name (str): Name of the student
        photo_dir (pathlib.Path): Path to a directory with photos.
    """
    try:
        pattern = name + ".*"
        nfc = unicodedata.normalize("NFC", pattern)
        nfd = unicodedata.normalize("NFD", pattern)
        return next(itertools.chain(photo_dir.glob(nfc), photo_dir.glob(nfd)))
    except StopIteration:
        console = Console(stderr=True)
        console.print(f"[red]WARNING: no photo found for {name}.")
        return None
