from canvas_course_tools.utils import get_canvas

canvas = get_canvas("vu")

courses = canvas.list_courses()

course = canvas.get_course(85692)
print(f"{canvas.list_groupsets(course)=}")
