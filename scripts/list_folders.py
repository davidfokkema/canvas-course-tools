import time

from canvas_course_tools.utils import find_course

canvas, course = find_course("mnw2")

for i in range(2):
    for folder in canvas.get_folders(course):
        print(folder.full_name)
    time.sleep(1)
    print(40 * "#")
