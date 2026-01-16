from canvas_course_tools.utils import get_canvas

canvas = get_canvas("vu")

courses = canvas.list_courses()

print(f"{canvas.get_course(courses[0].id)=}")
