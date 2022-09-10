import dateutil
from canvasapi import Canvas
from canvasapi.exceptions import Forbidden, InvalidAccessToken, ResourceDoesNotExist


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
            canvas_course (canvas.Course): a Canvas Course object

        Returns:
            dict: a custom course object
        """
        return {
            "id": canvas_course.id,
            "name": canvas_course.name,
            "course_code": canvas_course.course_code,
            "academic_year": academic_year_from_time(canvas_course.start_at),
        }


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
