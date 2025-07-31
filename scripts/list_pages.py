import time

from canvas_course_tools.utils import find_course

canvas, course = find_course("test")

for i in range(2):
    for page in canvas.get_pages(course):
        print(page.url, page.title)
    print(40 * "#")
    time.sleep(1)
