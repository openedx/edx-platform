# ======== Utility functions to help with population ===================================================================

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata

def get_assignment_to_problem_map(course_id):
    """
    Returns a dictionary with assignment types/categories as keys and the value is an array of arrays. Each inner array
    holds problem ids for an assignment. The arrays are ordered in the outer array as they are seen in the course, which
    is how they are numbered in a student's progress page.
    """

    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)

    assignment_problems_map = {}
    for section in course.get_children():
        for subsection in section.get_children():
            subsection_metadata = own_metadata(subsection)
            if ('graded' in subsection_metadata) and subsection_metadata['graded']:
                category = subsection_metadata['format']
                problems = []
                for unit in subsection.get_children():
                    for child in unit.get_children():
                        if child.location.category == 'problem':
                            problems.append(child.location.url())
                
                if category not in assignment_problems_map:
                    assignment_problems_map[category] = []
                    
                assignment_problems_map[category].append(problems)

    return assignment_problems_map


def approx_equal(a,b,tolerance=0.0001):
    """
    Checks if a and b are at most the specified tolerance away from each other.
    """
    return abs(a-b) <= tolerance;
