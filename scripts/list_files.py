from canvas_course_tools.utils import find_course

canvas, course = find_course("mnw2")

for file in canvas.get_files(course, batch_size=100):
    assert file.folder is not None, "File must have a folder"
    print(file.folder.full_name / file.filename)
