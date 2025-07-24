from canvas_course_tools.utils import find_course

canvas, course = find_course("mnw2")

for folder in canvas.get_folders(course):
    print(folder.full_name)
