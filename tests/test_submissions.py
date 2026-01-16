from rich.pretty import pprint

from canvas_course_tools.utils import find_course

canvas, course = find_course("ecpc25")
(group,) = [g for g in canvas.get_assignment_groups(course=course) if "ECPC" in g.name]
assignment = canvas.get_assignments_for_group(group)[0]
pprint(assignment)
(student,) = [
    u
    for u in canvas.get_students(course_id=course.id, show_test_student=True)
    if "Test" in u.name
]
submissions = canvas.get_submissions(assignment=assignment, student=student)
pprint(submissions)
