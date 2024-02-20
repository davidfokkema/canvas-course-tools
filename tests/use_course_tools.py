from canvas_course_tools import group_lists

# example data which can be loaded from a file
CONTENTS = """\
# Physics 101
## Group A
Drew Ferrell (800057) [second year]
Amanda James (379044)
Antonio Morris (804407) [skips thursdays]
"""

if __name__ == "__main__":
    grouping = group_lists.parse_group_list(CONTENTS)
    print("FIRST PAGE")
    for experiment in grouping.groups:
        print(f"EXPERIMENT: {experiment.name}")
        for student in experiment.students:
            # sortable_name is only used by the Canvas LMS
            print(f"STUDENT {student.id}: {student.name}")
        print(f"EXPERIMENT COMPLETED")
    print("LAST PAGE")
