from dataclasses import dataclass
from typing import List

import dateutil.parser
from canvasapi import Canvas
from canvasapi.exceptions import Forbidden, InvalidAccessToken, ResourceDoesNotExist


@dataclass(frozen=True)
class Student:
    id: int
    name: str
    sortable_name: str


@dataclass(frozen=True)
class Section:
    id: int
    name: str
    students: List[Student]


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
        return [self._make_course_object(course) for course in courses]

    def get_course(self, course_id):
        """Get a Canvas course by id.

        Args:
            course_id: a Canvas course id.

        Returns:
            A Canvas course object.
        """
        return self._make_course_object(self.canvas.get_course(course_id))

    def _make_course_object(self, canvas_course):
        """Make a course object from a Canvas Course.

        Build a custom course object with only the fields we actually use and
        added custom fields like 'academic_year'.

        Args:
            canvas_course (canvas.Course): a Canvas Course object.

        Returns:
            dict: a custom course object with fields id, name, course_code and
                academic_year.
        """
        return {
            "id": canvas_course.id,
            "name": canvas_course.name,
            "course_code": canvas_course.course_code,
            "academic_year": academic_year_from_time(canvas_course.start_at),
        }

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
