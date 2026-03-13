from rich.pretty import pprint

from canvas_course_tools.utils import find_course

canvas, course = find_course("ecpc25")
(group,) = [g for g in canvas.get_assignment_groups(course=course) if "ECPC" in g.name]
for assignment in canvas.get_assignments_for_group(group):
    pprint(assignment)
    submissions = canvas.get_submissions(assignment=assignment)
    pprint(submissions)
