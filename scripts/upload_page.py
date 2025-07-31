from pathlib import Path

from canvas_course_tools.utils import find_course

canvas, course = find_course("test")
page = canvas.upload_markdown_page(
    course, content=(Path(__file__).parent / "testdoc.md").read_text()
)
print(page)
