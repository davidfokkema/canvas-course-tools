from dataclasses import dataclass, field
from typing import Optional

import dateutil.parser
from canvasapi import Canvas
from canvasapi.exceptions import Forbidden, InvalidAccessToken, ResourceDoesNotExist
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


class CanvasTasks:

    """Collection of canvas-related tasks."""

    def __init__(self, url, token):
        """Initialize the class.

        Args:
            url: a string containing the Canvas server URL
            token: a string containing the Canvas API access token
        """
        self.canvas = Canvas(url, token)

    def list_courses(self):
        """List Canvas courses.

        Returns:
            A list of Canvas course objects.
        """
        courses = self.canvas.get_courses()
        return [
            Course(
                id=course.id,
                name=course.name,
                course_code=course.course_code,
                _start=course.start_at,
            )
            for course in courses
        ]

    def get_course(self, course_id):
        """Get a Canvas course by id.

        Args:
            course_id: a Canvas course id.

        Returns:
            A Canvas course object.
        """
        course = self.canvas.get_course(course_id)
        return Course(
            id=course.id,
            name=course.name,
            course_code=course.course_code,
            _start=course.start_at,
        )

    def get_students(self, course_id):
        """Get all students in a course.

        Args:
            course_id (integer): the Canvas course id

        Returns:
            list: a list of student objects
        """
        course = self.canvas.get_course(course_id)
        students = course.get_users(enrollment_type=["student"])
        return [
            Student(
                id=student.id,
                name=student.short_name,
                sortable_name=student.sortable_name,
            )
            for student in students
        ]

    def get_sections(self, course_id):
        """Get a list of sections, including students

        Args:
            course_id (int): the course id

        Returns:
            List[Section]: A list of Sections
        """
        course = self.canvas.get_course(course_id)
        sections = course.get_sections(include=["students"])
        return [
            Section(
                id=section.id,
                name=section.name,
                students=[
                    Student(
                        id=student["id"],
                        name=student["short_name"],
                        sortable_name=student["sortable_name"],
                    )
                    for student in section.students
                ],
            )
            for section in sections
            if section.students is not None
        ]


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
