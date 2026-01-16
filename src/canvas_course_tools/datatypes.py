import pathlib
from dataclasses import dataclass, field

import canvasapi
from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class Course(BaseModel):
    id: int
    name: str
    course_code: str
    term: str
    alias: str | None = None

    @field_validator("term", mode="before")
    @classmethod
    def term_to_str(cls, v):
        if isinstance(v, dict) and "name" in v:
            return v["name"]
        return v


class GroupSet(BaseModel):
    id: int
    name: str


class Group(BaseModel):
    id: int
    name: str


class Student(BaseModel):
    id: int
    # The API returns 'short_name', which we map to 'name'
    name: str = Field(validation_alias="short_name")
    sortable_name: str | None = None
    first_name: str = ""
    last_name: str = ""
    notes: str | None = None
    photo: pathlib.Path | None = None

    @model_validator(mode="after")
    def set_first_last_name(self) -> "Student":
        """Parse full name into first and last names."""
        # Replace underscores used to group multi-word names
        parsed_name = self.name.replace("_", " ")
        self.first_name, _, self.last_name = parsed_name.partition(" ")
        self.name = parsed_name
        return self


class Section(BaseModel):
    id: int
    name: str
    students: list[Student] = []


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
