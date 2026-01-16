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

    def _get_single_object(
        self,
        path: str,
        model: Type[BaseModel],
        params: dict | None = None,
        context: dict | None = None,
    ) -> BaseModel:
        """Get a single object from an API endpoint.
        
        Args:
            path: The API endpoint path.
            model: The Pydantic model to validate the response against.
            params: Optional query parameters.
            context: Optional validation context to pass to Pydantic.
            
        Returns:
            A validated Pydantic model instance.
        """
        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return model.model_validate(response.json(), context=context)

    def _post_object(
        self,
        path: str,
        model: Type[BaseModel],
        json: dict | None = None,
        context: dict | None = None,
    ) -> BaseModel:
        """Create an object via POST request to an API endpoint.
        
        Args:
            path: The API endpoint path.
            model: The Pydantic model to validate the response against.
            json: Optional JSON body for the POST request.
            context: Optional validation context to pass to Pydantic.
            
        Returns:
            A validated Pydantic model instance.
        """
        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            response = client.post(path, json=json)
            response.raise_for_status()
            return model.model_validate(response.json(), context=context)

    def _post_no_response(self, path: str, json: dict | None = None) -> None:
        """Send a POST request that doesn't require a validated response.
        
        Args:
            path: The API endpoint path.
            json: Optional JSON body for the POST request.
        """
        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            response = client.post(path, json=json)
            response.raise_for_status()

    def _delete_object(self, path: str) -> None:
        """Delete an object via DELETE request to an API endpoint.
        
        Args:
            path: The API endpoint path.
        """
        with httpx.Client(base_url=self._url, headers=self._headers) as client:
            response = client.delete(path)
            response.raise_for_status()

    def _get_paginated_list(
        self,
        path: str,
        model: Type[BaseModel],
        params: dict | None = None,
        context: dict | None = None,
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
                items.extend(
                    [
                        model.model_validate(item, context=context)
                        for item in response.json()
                    ]
                )

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
        return self._get_single_object(
            f"/api/v1/courses/{course_id}",
            Course,
            params={"include[]": "term"}
        )

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

        for groupset in existing_groupsets:
            if groupset.name == name:
                if not overwrite:
                    raise CanvasObjectExistsError("Groupset already exists.")
                else:
                    self._delete_object(f"/api/v1/group_categories/{groupset.id}")

        return self._post_object(
            f"/api/v1/courses/{course.id}/group_categories",
            GroupSet,
            json={"name": name}
        )

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
            group_set_id: The groupset ID.

        Returns:
            The requested GroupSet object.
        """
        return self._get_single_object(
            f"/api/v1/group_categories/{group_set_id}",
            GroupSet
        )

    def create_group(self, group_name: str, group_set: GroupSet) -> Group:
        """Create a group inside a GroupSet.

        Args:
            group_name: Name of the group to create.
            group_set: The GroupSet in which the group will be created.

        Returns:
            The newly created Group object.
        """
        return self._post_object(
            f"/api/v1/group_categories/{group_set.id}/groups",
            Group,
            json={"name": group_name}
        )

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
        self._post_no_response(
            f"/api/v1/groups/{group.id}/memberships",
            json={"user_id": student.id}
        )

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
        """Get all assignment groups in a course.

        Args:
            course: The course object.

        Returns:
            A list of AssignmentGroup objects.
        """
        path = f"/api/v1/courses/{course.id}/assignment_groups"
        return self._get_paginated_list(
            path, AssignmentGroup, context={"course": course}
        )

    def get_assignments_for_group(self, group: AssignmentGroup) -> list[Assignment]:
        """Get all assignments in an assignment group.

        Args:
            group: The assignment group object.

        Returns:
            A list of Assignment objects.
        """
        path = f"/api/v1/courses/{group.course.id}/assignment_groups/{group.id}/assignments"
        return self._get_paginated_list(
            path, Assignment, context={"course": group.course}
        )

    def get_submissions(
        self, assignment: Assignment, student: Student
    ) -> CanvasSubmission:
        """Get student submission.

        Gets a student submission from Canvas for a particular assignment. The
        submission includes all submission attempts along with all submission
        comments, either by the student or by teachers or teaching assistants.

        Args:
            assignment: The assignment for which to get the submission.
            student: The student for whom to get the submission.

        Returns:
            The student submission.
        """
        path = f"/api/v1/courses/{assignment.course.id}/assignments/{assignment.id}/submissions/{student.id}"
        params = {"include[]": ["submission_history", "submission_comments"]}
        return self._get_single_object(path, CanvasSubmission, params=params)
