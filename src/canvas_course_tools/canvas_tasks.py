import pathlib
from typing import Any, Generator

import canvasapi
import httpx
import mistune
from bs4 import BeautifulSoup
from canvasapi import Canvas
from canvasapi.exceptions import Forbidden, InvalidAccessToken, ResourceDoesNotExist
from pydantic import TypeAdapter

from canvas_course_tools.datatypes import (
    Assignment,
    AssignmentGroup,
    CanvasFile,
    CanvasFolder,
    CanvasPage,
    CanvasSubmission,
    Course,
    Group,
    GroupSet,
    Section,
    Student,
)

__all__ = ["Forbidden", "InvalidAccessToken", "ResourceDoesNotExist"]


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
        self._folders_cache: dict[Course, dict[int, CanvasFolder]] = {}
        self._files_cache: dict[Course, dict[int, CanvasFile]] = {}
        self._pages_cache: dict[Course, dict[int, CanvasPage]] = {}

    def list_courses(self):
        """List Canvas courses.

        Returns:
            A list of Canvas course objects.
        """
        courses = self.canvas.get_courses(include=["term"])
        return [create_course_object(course) for course in courses]

    def get_course(self, course_id):
        """Get a Canvas course by id.

        Args:
            course_id: a Canvas course id.

        Returns:
            A Canvas course object.
        """
        course = self.canvas.get_course(course_id, include=["term"])
        return create_course_object(course)

    def get_students(self, course_id, show_test_student=False):
        """Get all students in a course.

        Args:
            course_id (integer): the Canvas course id
            show_test_student (bool): if True, include the Test Student

        Returns:
            list: a list of student objects
        """
        course = self.canvas.get_course(course_id)
        if show_test_student:
            enrollment_type = ["student", "student_view"]
        else:
            enrollment_type = ["student"]
        students = course.get_users(enrollment_type=enrollment_type)
        return [create_student_object(student) for student in students]

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

    def list_groupsets(self, course: Course) -> list[GroupSet]:
        """List groupsets in a course.

        Args:
            course (Course): the course containing the groupsets.

        Returns:
            list[GroupSet]: a list of GroupSet objects.
        """
        groupsets = course._course.get_group_categories()
        return [
            GroupSet(id=groupset.id, name=groupset.name, _group_set=groupset)
            for groupset in groupsets
        ]

    def get_groupset(self, group_set_id: int) -> GroupSet:
        """Get a groupset by id

        Args:
            group_set_id (int): the groupset ID.

        Returns:
            GroupSet: the requests groupset object.
        """
        groupset = self.canvas.get_group_category(group_set_id)
        return GroupSet(id=groupset.id, name=groupset.name, _group_set=groupset)

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

    def list_groups(self, group_set: GroupSet) -> list[Group]:
        groups = group_set._group_set.get_groups()
        return [Group(id=group.id, name=group.name, _group=group) for group in groups]

    def add_student_to_group(self, student, group):
        """Add student to a group.

        Args:
            student (Student): the student to add to the group.
            group (Group): the group in which to place the student.
        """
        canvas_group = self.canvas.get_group(group.id)
        canvas_group.create_membership(student.id)

    def get_students_in_group(self, group: Group) -> list[Student]:
        students = group._group.get_users()
        return [create_student_object(student) for student in students]

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
        response.raise_for_status()
        return CanvasSubmission.model_validate_json(response.text)

    def get_folders(
        self, course: Course, batch_size: int | None = None
    ) -> Generator[CanvasFolder, None, None]:
        """Get all folders in a course.

        Args:
            course: the course for which to get the folders.
            batch_size: the number of folders to fetch per request. If None,
                will default to the Canvas API default.

        Yields:
            A generator yielding CanvasFolder objects.
        """
        if course in self._folders_cache:
            yield from self._folders_cache[course].values()
            return

        url = f"{self._url}/api/v1/courses/{course.id}/folders"
        self._folders_cache[course] = {}
        adapter = TypeAdapter(list[CanvasFolder])
        for response in self._get_paginated_api_response(
            url, params={"per_page": batch_size} if batch_size else None
        ):
            for folder in adapter.validate_json(response):
                self._folders_cache[course][folder.id] = folder
                yield folder

    def get_folder_by_id(self, folder_id: int) -> CanvasFolder:
        """Get a folder by its ID.

        Args:
            folder_id: the ID of the folder to retrieve.

        Returns:
            The requested CanvasFolder object.
        """
        if not self._folders_cache:
            raise ValueError("Folders cache is empty. Call get_folders first.")

        for course_folders in self._folders_cache.values():
            if folder_id in course_folders:
                return course_folders[folder_id]

        raise ValueError(
            f"Folder with ID {folder_id} not found. Call get_folders first."
        )

    def get_files(
        self, course: Course, batch_size: int | None = None
    ) -> Generator[CanvasFile, None, None]:
        """Get all files in a course.

        Args:
            course: the course for which to get the files.
            batch_size: the number of files to fetch per request. If None,
                will default to the Canvas API default.

        Yields:
            A generator yielding CanvasFile objects.
        """
        if course in self._files_cache:
            yield from self._files_cache[course].values()
            return

        if course not in self._folders_cache:
            # Fetching folders before files.
            for _ in self.get_folders(course, batch_size):
                pass

        url = f"{self._url}/api/v1/courses/{course.id}/files"
        self._files_cache[course] = {}
        adapter = TypeAdapter(list[CanvasFile])
        for response in self._get_paginated_api_response(
            url, params={"per_page": batch_size} if batch_size else None
        ):
            for file in adapter.validate_json(response):
                file.folder = self.get_folder_by_id(file.folder_id)
                self._files_cache[course][file.id] = file
                yield file

    def get_pages(
        self, course: Course, batch_size: int | None = None
    ) -> Generator[CanvasPage, None, None]:
        """Get all pages in a course.

        Args:
            course: the course for which to get the pages.
            batch_size: the number of pages to fetch per request. If None,
                will default to the Canvas API default.

        Yields:
            A generator yielding CanvasPages objects.
        """
        if course in self._pages_cache:
            yield from self._pages_cache[course].values()
            return

        url = f"{self._url}/api/v1/courses/{course.id}/pages"
        self._pages_cache[course] = {}
        adapter = TypeAdapter(list[CanvasPage])
        for response in self._get_paginated_api_response(
            url, params={"per_page": batch_size} if batch_size else None
        ):
            for page in adapter.validate_json(response):
                self._pages_cache[course][page.id] = page
                yield page

    def get_pages_by_title(self, course: Course, title: str) -> list[CanvasPage]:
        """Get all pages matching the title.

        Args:
            course: the course containing the pages.
            title: the title of the pages to retrieve.

        Returns:
            A list with all matching CanvasPage objects.
        """
        if course not in self._pages_cache:
            for _ in self.get_pages(course):
                pass

        return [
            page for page in self._pages_cache[course].values() if page.title == title
        ]

    def get_page_by_title(self, course: Course, title: str) -> CanvasPage:
        """Get a page by its title.

        Unline get_pages_by_title, this method only returns the first page that
        matches and raises an error if no page is found.

        Args:
            course: the course containing the page.
            title: the title of the page to retrieve.

        Returns:
            The requested CanvasPage object.

        Raises:
            ResourceDoesNotExist: if no page with the given title is found.
        """
        pages = self.get_pages_by_title(course, title)
        if not pages:
            raise ResourceDoesNotExist(f"Page with title '{title}' not found.")
        return pages[0]

    def _get_paginated_api_response(
        self, url: str, params: dict[str, Any] | None = None
    ) -> Generator[str, None, None]:
        """Get paginated API response.

        Args:
            url: the URL to fetch.
            params: additional parameters to include in the request.

        Yields:
            A string with the response text.
        """
        full_url = httpx.URL(url).copy_merge_params(params or {})
        while True:
            response = httpx.get(url=full_url, headers=self._headers)
            response.raise_for_status()
            yield response.text

            if (
                "Link" not in response.headers
                or (next_page := response.links.get("next", {}).get("url")) is None
            ):
                break
            full_url = httpx.URL(next_page)

    def upload_file(
        self,
        course: Course,
        file_path: pathlib.Path,
        folder_path: pathlib.Path | None = None,
        overwrite: bool = False,
    ) -> None:
        """Upload a file to a specific folder in a course.

        Args:
            course: the course to which the file will be uploaded.
            file_path: the path to the file to upload.
            folder_path: the path to the folder in which to upload the file.
            overwrite: whether to overwrite an existing file with the same name.
        """
        # See https://developerdocs.instructure.com/services/canvas/basics/file.file_uploads
        #
        # Step 1: Telling Canvas about the file upload and getting a token
        response = httpx.post(
            f"{self._url}/api/v1/courses/{course.id}/files",
            headers=self._headers,
            params={
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "parent_folder_path": folder_path.as_posix() if folder_path else None,
                "on_duplicate": "overwrite" if overwrite else "rename",
            },
        )
        response.raise_for_status()

        # Step 2: Upload the file data to the URL given in the previous response
        response_data = response.json()
        url = response_data["upload_url"]
        params = response_data.get("upload_params", {})
        file = {"file": file_path.open("rb")}
        response = httpx.post(url, data=params, files=file)
        response.raise_for_status()

        # Step 3: Confirm the upload's success
        if response.is_redirect:
            print("REDIRECTION TO CONFIRM UPLOAD")
            assert response.next_request is not None, (
                "Next request should be provided by Canvas API"
            )
            client = httpx.Client(headers=self._headers)
            response = client.send(response.next_request)
            response.raise_for_status()
        else:
            # If the response is not a redirect, we expect a 201 Created status
            assert response.status_code == 201, (
                f"Expected 201 Created, got {response.status_code}"
            )

    def upload_markdown_page(self, course: Course, content: str) -> CanvasPage:
        """Upload a markdown page to a course.

        The Markdown content will be converted to HTML before uploading. The
        page title will be derived from the <h1> tag in the content. If no <h1>
        tag is present an exception will be raised.

        This method first searches for an existing page with the same title, and
        will update the first page that matches if any exist. If no such page
        exists, it will create a new page.


        Args:
            course: the course to which the page will be uploaded.
            content: the markdown content of the page.

        Returns:
            The created CanvasPage object.

        Raises:
            ValueError: The markdown does not conform to the expected structure.
        """
        # Convert Markdown to HTML and extract the title
        markdown = mistune.create_markdown(
            escape=False,
            plugins=["math", "footnotes", "superscript"],
        )
        html = markdown(content)
        assert type(html) is str, "Something went wrong with the markdown conversion"
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        if h1 is None:
            raise ValueError(
                "Markdown content must contain a heading level 1 or an <h1> tag for the title."
            )
        title = h1.text.strip()
        h1.decompose()

        try:
            old_page = self.get_page_by_title(course, title)
            method, url = (
                "PUT",
                f"{self._url}/api/v1/courses/{course.id}/pages/{old_page.short_url}",
            )
        except ResourceDoesNotExist:
            method, url = "POST", f"{self._url}/api/v1/courses/{course.id}/pages"
        response = httpx.request(
            method,
            url,
            headers=self._headers,
            params={"wiki_page[title]": title, "wiki_page[body]": str(soup)},
        )
        response.raise_for_status()
        return CanvasPage.model_validate_json(response.text)


def create_course_object(course: canvasapi.course.Course):
    return Course(
        id=course.id,
        name=course.name,
        course_code=course.course_code,
        term=course.term["name"],
        _course=course,
    )


def create_student_object(student: canvasapi.user.User):
    return Student(
        id=student.id,
        name=student.short_name,
        sortable_name=student.sortable_name,
    )
