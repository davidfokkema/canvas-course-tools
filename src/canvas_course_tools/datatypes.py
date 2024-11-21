import pathlib
from dataclasses import dataclass, field

import canvasapi
from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    Field,
    HttpUrl,
    ValidationInfo,
    field_validator,
)


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


class Attachment(BaseModel):
    id: int
    filename: str
    url: HttpUrl
    content_type: str = Field(
        validation_alias=AliasChoices("content_type", "content-type")
    )


class SubmissionAttempt(BaseModel):
    id: int
    attempt: int
    submitted_at: AwareDatetime
    seconds_late: int
    attachments: list[Attachment]


class Comment(BaseModel):
    id: int
    author_name: str
    created_at: AwareDatetime
    comment: str


class Submission(BaseModel):
    id: int
    grade: str | None
    score: float | None
    missing: bool
    attempts: list[SubmissionAttempt] = Field(
        validation_alias=AliasChoices("attempts", "submission_history")
    )
    comments: list[Comment] = Field(
        validation_alias=AliasChoices("comments", "submission_comments")
    )

    @field_validator("attempts", mode="before")
    @classmethod
    def check_missing(
        cls, value: dict, info: ValidationInfo
    ) -> list[SubmissionAttempt]:
        """Check if the submission is missing."""
        if info.data["missing"]:
            return []
        else:
            return value
