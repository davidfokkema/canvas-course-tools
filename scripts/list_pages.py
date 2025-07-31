import time

from canvas_course_tools.utils import find_course

canvas, course = find_course("test")

for i in range(2):
    for page in canvas.get_pages(course):
        print(page.short_url, page.title)
    print(40 * "#")
    time.sleep(1)

page = canvas.get_page_by_title(course, "A fancy new page")
print(page)
