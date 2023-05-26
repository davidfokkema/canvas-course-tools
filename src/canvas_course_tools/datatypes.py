import pathlib
from dataclasses import dataclass, field

import canvasapi


@dataclass
class Course:
    id: int
    name: str
    course_code: str
    term: str
    alias: str | None = None
    _course: canvasapi.course.Course | None = field(default=None, repr=False)


@dataclass
class GroupSet:
    id: int
    name: str
    _group_set: canvasapi.group.GroupCategory | None = field(default=None, repr=False)


@dataclass
class Group:
    id: int
    name: str
    _group: canvasapi.group.Group | None = field(default=None, repr=False)


@dataclass
class Student:
    id: int
    name: str
    sortable_name: str | None = None
    first_name: str = field(init=False)
    last_name: str = field(init=False)
    notes: str | None = None
    photo: pathlib.Path | None = None

    def __post_init__(self):
        # Parse human names, allowing for underscores to group parts of the name
        self.first_name, _, self.last_name = self.name.partition(" ")
        self.first_name = self.first_name.replace("_", " ")
        self.name = self.name.replace("_", " ")


@dataclass
class Section:
    id: int
    name: str
    students: list[Student]


@dataclass
class StudentGroup:
    name: str = ""
    students: list[Student] = field(default_factory=list)


@dataclass
class GroupList:
    name: str = ""
    groups: list[StudentGroup] = field(default_factory=list)
