import hashlib
from typing import Type

import canvasapi
import httpx
from canvasapi import Canvas
from canvasapi.exceptions import Forbidden, InvalidAccessToken, ResourceDoesNotExist
from pydantic import BaseModel

from canvas_course_tools.datatypes import (
    Assignment,
    AssignmentGroup,
    CanvasSubmission,
    Course,
    Group,
    GroupSet,
    Section,
    Student,
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
        self._url = url
        self._headers = {"Authorization": f"Bearer {token}"}

    def __str__(self) -> str:
        return f"Canvas server at {self._url}"

    def __repr__(self) -> str:
        return f"CanvasTasks({self._url})"

    def _get_paginated_list(
        self, path: str, model: Type[BaseModel], params: dict | None = None
    ) -> list:
        """Get a list of objects from a paginated API endpoint."""
        items = []
        url = path
        # Use a copy of params so we can modify it for the first request
        request_params = params.copy() if params else {}
        request_params["per_page"] = 100

        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            while url:
                response = client.get(url, params=request_params)
                response.raise_for_status()
                items.extend([model.model_validate(item) for item in response.json()])

                url = response.links.get("next", {}).get("url")
                # Subsequent requests use the opaque URL, so no params are needed.
                if request_params:
                    request_params = None
        return items

    def list_courses(self) -> list[Course]:
        """List all Canvas courses, handling pagination.

        Returns:
            A list of all available Canvas course objects.
        """
        return self._get_paginated_list(
            "/api/v1/courses", Course, params={"include[]": "term"}
        )

    def get_course(self, course_id: int) -> Course:
        """Get a Canvas course by id.

        Args:
            course_id: The ID of the Canvas course.

        Returns:
            A Canvas course object.
        """
        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            response = client.get(
                f"/api/v1/courses/{course_id}", params={"include[]": "term"}
            )
            response.raise_for_status()
            return Course.model_validate(response.json())

    def get_students(
        self, course_id: int, show_test_student: bool = False
    ) -> list[Student]:
        """Get all students in a course.

        Args:
            course_id: The ID of the Canvas course.
            show_test_student: If True, include the "Test Student" in the results.

        Returns:
            A list of Student objects.
        """
        path = f"/api/v1/courses/{course_id}/users"
        if show_test_student:
            params = {"enrollment_type[]": ["student", "student_view"]}
        else:
            params = {"enrollment_type[]": ["student"]}

        return self._get_paginated_list(path, Student, params=params)

    def get_sections(self, course_id: int) -> list[Section]:
        """Get a list of sections, including students.

        Args:
            course_id: The ID of the Canvas course.

        Returns:
            A list of Section objects, each potentially containing a list of Students.
        """
        path = f"/api/v1/courses/{course_id}/sections"
        params = {"include[]": ["students"]}
        return self._get_paginated_list(path, Section, params=params)

    def create_groupset(self, name: str, course: Course, overwrite: bool) -> GroupSet:
        """Create a groupset in a course.

        Args:
            name: Name of the groupset.
            course: The course in which to create the groupset.
            overwrite: If True, delete any existing groupset with the same name.

        Returns:
            The newly created GroupSet object.
        """
        existing_groupsets = self.list_groupsets(course)

        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            for groupset in existing_groupsets:
                if groupset.name == name:
                    if not overwrite:
                        raise CanvasObjectExistsError("Groupset already exists.")
                    else:
                        # Issue a DELETE request
                        delete_resp = client.delete(
                            f"/api/v1/group_categories/{groupset.id}"
                        )
                        delete_resp.raise_for_status()

            # Issue a POST request to create the new groupset
            create_resp = client.post(
                f"/api/v1/courses/{course.id}/group_categories",
                json={"name": name},
            )
            create_resp.raise_for_status()
            return GroupSet.model_validate(create_resp.json())

    def list_groupsets(self, course: Course) -> list[GroupSet]:
        """List groupsets in a course.

        Args:
            course: The course object containing the groupsets.

        Returns:
            A list of GroupSet objects.
        """
        path = f"/api/v1/courses/{course.id}/group_categories"
        return self._get_paginated_list(path, GroupSet)

    def get_groupset(self, group_set_id: int) -> GroupSet:
        """Get a groupset by id

        Args:
            group_set_id (int): the groupset ID.

        Returns:
            GroupSet: the requests groupset object.
        """
        groupset = self.canvas.get_group_category(group_set_id)
        return GroupSet(id=groupset.id, name=groupset.name)

    def create_group(self, group_name: str, group_set: GroupSet) -> Group:
        """Create a group inside a GroupSet.

        Args:
            group_name: Name of the group to create.
            group_set: The GroupSet in which the group will be created.

        Returns:
            The newly created Group object.
        """
        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            response = client.post(
                f"/api/v1/group_categories/{group_set.id}/groups",
                json={"name": group_name},
            )
            response.raise_for_status()
            return Group.model_validate(response.json())

    def list_groups(self, group_set: GroupSet) -> list[Group]:
        """List groups in a groupset.

        Args:
            group_set: The groupset object containing the groups.

        Returns:
            A list of Group objects.
        """
        path = f"/api/v1/group_categories/{group_set.id}/groups"
        return self._get_paginated_list(path, Group)

    def add_student_to_group(self, student: Student, group: Group) -> None:
        """Add a student to a group.

        Args:
            student: The student to add to the group.
            group: The group in which to place the student.
        """
        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            response = client.post(
                f"/api/v1/groups/{group.id}/memberships",
                json={"user_id": student.id},
            )
            response.raise_for_status()

    def get_students_in_group(self, group: Group) -> list[Student]:
        """Get a list of all students in a particular group.

        Args:
            group: The group object from which to get students.

        Returns:
            A list of Student objects.
        """
        path = f"/api/v1/groups/{group.id}/users"
        return self._get_paginated_list(path, Student)

    def get_assignment_groups(self, course: Course) -> list[AssignmentGroup]:
        groups = course._course.get_assignment_groups()
        return [
            AssignmentGroup(id=group.id, name=group.name, course=course)
            for group in groups
        ]

    def get_assignments_for_group(self, group: AssignmentGroup) -> list[Assignment]:
        assignments = group.course._course.get_assignments_for_group(group.id)
        return [
            Assignment(
                id=assignment.id,
                name=assignment.name,
                course=group.course,
                submission_types=assignment.submission_types,
                _api=assignment,
            )
            for assignment in assignments
        ]

    def get_submissions(
        self, assignment: Assignment, student: Student
    ) -> CanvasSubmission:
        """Get student submission.

        Gets a student submission from Canvas for a particular assignment. The
        submission includes all submission attempts along with all submission
        comments, either by the student or by teachers or teaching assistants.

        Args:
            assignment (Assignment): the assignment for which to get the
            submission. student (Student): the student for whom to get the
            submission.

        Returns:
            Submission: the student submission
        """
        response = httpx.get(
            f"{self._url}/api/v1/courses/{assignment.course.id}/assignments/{assignment.id}/submissions/{student.id}",
            headers=self._headers,
            params={"include[]": ["submission_history", "submission_comments"]},
        )
        return CanvasSubmission.model_validate_json(response.text)
