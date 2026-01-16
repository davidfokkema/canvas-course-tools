import pathlib

from pydantic import (
    AliasChoices,
    AwareDatetime,
    BaseModel,
    Field,
    HttpUrl,
    ValidationInfo,
    field_validator,
    model_validator,
)


class Course(BaseModel):
    id: int
    name: str = ""
    course_code: str
    term: str
    alias: str | None = None

    @field_validator("term", mode="before")
    @classmethod
    def term_to_str(cls, v):
        if isinstance(v, dict) and "name" in v:
            return v["name"]
        return v


class AssignmentGroup(BaseModel):
    id: int
    name: str
    course: Course

    @model_validator(mode="before")
    @classmethod
    def add_course_from_context(cls, data, info: ValidationInfo):
        """
        Populates the 'course' field from the validation context.
        This validator runs before individual fields are validated.
        """
        if isinstance(data, dict):
            # Only add course if it's not already in the data
            if "course" not in data:
                if info.context and "course" in info.context:
                    # Make a copy to avoid mutating the original
                    data = data.copy()
                    data["course"] = info.context["course"]
                else:
                    raise ValueError(
                        "AssignmentGroup requires 'course' in validation context"
                    )
        return data


class GroupSet(BaseModel):
    id: int
    name: str


class Group(BaseModel):
    id: int
    name: str


class Student(BaseModel):
    id: int
    # The API returns 'short_name', but we also want to allow 'name' for direct instantiation.
    name: str = Field(validation_alias=AliasChoices("short_name", "name"))
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

    @field_validator("students", mode="before")
    @classmethod
    def handle_null_students(cls, v):
        if v is None:
            return []
        else:
            return v


class StudentGroup(BaseModel):
    name: str = ""
    students: list[Student] = []


class GroupList(BaseModel):
    name: str = ""
    groups: list[StudentGroup] = []


class Assignment(BaseModel):
    id: int
    name: str
    course: Course
    submission_types: list[str]

    @model_validator(mode="before")
    @classmethod
    def add_course_from_context(cls, data, info: ValidationInfo):
        """
        Populates the 'course' field from the validation context.
        This validator runs before individual fields are validated.
        """
        if isinstance(data, dict):
            # Only add course if it's not already in the data
            if "course" not in data:
                if info.context and "course" in info.context:
                    # Make a copy to avoid mutating the original
                    data = data.copy()
                    data["course"] = info.context["course"]
                else:
                    raise ValueError(
                        "Assignment requires 'course' in validation context"
                    )
        return data


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
