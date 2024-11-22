import pathlib
from dataclasses import dataclass, field

import canvasapi
from pydantic import AliasChoices, AwareDatetime, BaseModel, Field, HttpUrl


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


@dataclass
class AssignmentGroup:
    id: int
    name: str
    course: Course


@dataclass
class Assignment:
    id: int
    name: str
    course: Course
    submission_types: list[str]
    _api: canvasapi.assignment.Assignment | None = field(default=None, repr=False)


class CanvasAttachment(BaseModel):
    id: int
    filename: str
    url: HttpUrl
    content_type: str = Field(
        validation_alias=AliasChoices("content_type", "content-type")
    )


class CanvasSubmissionAttempt(BaseModel):
    id: int
    attempt: int | None
    submitted_at: AwareDatetime | None
    seconds_late: int
    attachments: list[CanvasAttachment] = []


class CanvasComment(BaseModel):
    id: int
    author_name: str
    created_at: AwareDatetime
    comment: str


class CanvasSubmission(CanvasSubmissionAttempt):
    grade: str | None
    score: float | None
    attempt: int | None
    missing: bool
    attempts: list[CanvasSubmissionAttempt] = Field(
        validation_alias=AliasChoices("attempts", "submission_history")
    )
    comments: list[CanvasComment] = Field(
        validation_alias=AliasChoices("comments", "submission_comments")
    )
