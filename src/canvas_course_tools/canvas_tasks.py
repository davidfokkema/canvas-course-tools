from canvasapi import Canvas
from canvasapi.exceptions import Forbidden, InvalidAccessToken, ResourceDoesNotExist

from canvas_course_tools.datatypes import (
    Course,
    Section,
    Student,
    GroupSet,
    Group,
)


class CanvasObjectExistsError(Exception):
    pass


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

    def create_groupset(self, name, course, overwrite):
        """Create groupset in course.

        Args:
            name (string): name of the groupset
            course (Course): the course in which to create the groupset
            overwrite (bool): whether or not to overwrite an existing groupset

        Returns:
            GroupSet: the newly created groupset
        """
        canvas_course = self.canvas.get_course(course.id)
        groupsets = list(canvas_course.get_group_categories())
        groupset_names = [g.name for g in groupsets]
        if name in groupset_names:
            if not overwrite:
                raise CanvasObjectExistsError("Groupset already exists.")
            else:
                for groupset in [g for g in groupsets if g.name == name]:
                    # we don't expect groupset with the same name, but delete them all in any case
                    groupset.delete()
        groupset = canvas_course.create_group_category(name)
        return GroupSet(id=groupset.id, name=name)

    def create_group(self, group_name, group_set):
        """Create a group inside a GroupSet.

        Args:
            group_name (str): name of the group to create.
            group_set (GroupSet): the GroupSet in which the group will be
                created.

        Returns:
            Group: the newly created group.
        """
        groupset = self.canvas.get_group_category(group_set.id)
        group = groupset.create_group(name=group_name)
        return Group(id=group.id, name=group_name)

    def add_student_to_group(self, student, group):
        """Add student to a group.

        Args:
            student (Student): the student to add to the group.
            group (Group): the group in which to place the student.
        """
        canvas_group = self.canvas.get_group(group.id)
        canvas_group.create_membership(student.id)
