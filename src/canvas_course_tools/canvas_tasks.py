from canvasapi import Canvas


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
        """List Canvas courses."""
        courses = self.canvas.get_courses()
        return list(courses)