from dataclasses import dataclass, field
from typing import Optional

import dateutil.parser
from nameparser import HumanName


@dataclass
class Course:
    id: int
    name: str
    course_code: str
    academic_year: str = field(init=False)
    _start: str
    alias: Optional[str] = None

    def __post_init__(self):
        self.academic_year = academic_year_from_time(self._start)


@dataclass
class Student:
    id: int
    name: str
    sortable_name: Optional[str] = None
    first_name: str = field(init=False)
    last_name: str = field(init=False)

    def __post_init__(self):
        # Parse human names, allowing for underscores to group parts of the name
        name = HumanName(self.name)
        self.first_name = " ".join([name.first, name.middle]).rstrip()
        self.last_name = name.last.replace("_", " ")
        self.name = self.name.replace("_", " ")


@dataclass
class Section:
    id: int
    name: str
    students: list[Student]


def academic_year_from_time(time):
    """Return the academic year from a time string.

    Args:
        time: a string with a time in ISO format.
    """
    try:
        time = dateutil.parser.isoparse(time)
    except TypeError:
        return "Unknown"
    else:
        start_year = time.year
        if time.month < 8:
            start_year -= 1
        return f"{start_year}-{start_year + 1}"
