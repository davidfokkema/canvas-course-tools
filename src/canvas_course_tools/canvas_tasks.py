from canvasapi import Canvas
from canvasapi.exceptions import Forbidden, InvalidAccessToken, ResourceDoesNotExist

from canvas_course_tools.datatypes import Course, Section, Student


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
        courses = self.canvas.get_courses(include=["term"])
        return [
            Course(
                id=course.id,
                name=course.name,
                course_code=course.course_code,
                term=course.term["name"],
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
        course = self.canvas.get_course(course_id, include=["term"])
        return Course(
            id=course.id,
            name=course.name,
            course_code=course.course_code,
            term=course.term["name"],
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
