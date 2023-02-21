# canvas-course-tools

Canvas course tools was created at the physics practicals at the Vrije
Universiteit Amsterdam to greatly reduce the time needed to create class lists
(with photos!) for staff and teaching assistants. Class lists are also created
for students so that they can easily lookup their assigned experiments and TA's.
Furthermore, we use it to create student groups on Canvas for peer feedback.

This package provides the `canvas` command-line utility. After registering a
Canvas URL and API key (which you can generate on your profile settings page)
this tool allows you to list courses and students in different sections of your
courses. The output has a light markup and is ideally suited for saving as a
text file. It is then easy to copy and move lines inside the file to create
student groups. The file can then be parsed by the `canvas templates` command to
render templates based on the text file. This allows for creating class lists
(with short notes for each student) and even class lists with photos (if you
provide photos).

You can also use this tool to create groups and group sets on Canvas based on a
group list file.