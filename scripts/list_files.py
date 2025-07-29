from canvas_course_tools.utils import find_course

canvas, course = find_course("mnw2")

for file in canvas.get_files(course):
    print(file.filename)
