from pathlib import Path

from canvas_course_tools.utils import find_course

canvas, course = find_course("test")

canvas.upload_file(
    course, Path(__file__), folder_path=Path("my_uploads"), overwrite=True
)

for file in canvas.get_files(course, batch_size=100):
    assert file.folder is not None, "File must have a folder"
    print(
        Path(file.folder.full_name) / file.filename, Path(file.display_name), file.url
    )
