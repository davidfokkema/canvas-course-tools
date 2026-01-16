from canvas_course_tools.utils import get_canvas

canvas = get_canvas("vu")

print(f"{len(canvas.list_courses())=}")
