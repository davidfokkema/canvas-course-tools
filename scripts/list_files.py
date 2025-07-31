import time

from canvas_course_tools.utils import find_course

canvas, course = find_course("mnw2")

for i in range(2):
    for file in canvas.get_files(course):
        assert file.folder is not None, "File must have a folder"
        print(file.folder.full_name / file.filename)
    print(40 * "#")
    time.sleep(1)
