"""
Utility functions to help with population
"""

from datetime import datetime
from pytz import UTC
import logging
from optparse import make_option

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from queryable_student_module.models import Log

log = logging.getLogger("mitx.queryable")


def get_assignment_to_problem_map(course_id):
    """
    Returns a dictionary with assignment types/categories as keys and the value is an array of arrays. Each inner array
    holds problem ids for an assignment. The arrays are ordered in the outer array as they are seen in the course, which
    is how they are numbered in a student's progress page.
    """

    course = modulestore().get_instance(course_id, CourseDescriptor.id_to_location(course_id), depth=4)

    assignment_problems_map = {}
    for section in course.get_children():
        for subsection in section.get_children():
            subsection_metadata = own_metadata(subsection)
            if ('graded' in subsection_metadata) and subsection_metadata['graded']:
                category = subsection_metadata['format']
                if category not in assignment_problems_map:
                    assignment_problems_map[category] = []

                problems = []
                for unit in subsection.get_children():
                    for child in unit.get_children():
                        if child.location.category == 'problem':
                            problems.append(child.location.url())

                assignment_problems_map[category].append(problems)

    return assignment_problems_map


def approx_equal(first, second, tolerance=0.0001):
    """
    Checks if first and second are at most the specified tolerance away from each other.
    """
    return abs(first - second) <= tolerance


def pre_run_command(script_id, options, course_id):
    """
    Common pre-run method for both populate_studentgrades and populate_studentmoduleexpand commands.
    """

    log.info("--------------------------------------------------------------------------------")
    log.info("Populating queryable.{0} table for course {1}".format(script_id, course_id))
    log.info("--------------------------------------------------------------------------------")

    # Grab when we start, to log later
    tstart = datetime.now(UTC)

    iterative_populate = True
    last_log_run = {}
    if options['force']:
        log.info("--------------------------------------------------------------------------------")
        log.info("Full populate: Forced full populate")
        log.info("--------------------------------------------------------------------------------")
        iterative_populate = False

    if iterative_populate:
        # Get when this script was last run for this course
        last_log_run = Log.objects.filter(script_id__exact=script_id, course_id__exact=course_id)

        length = len(last_log_run)
        log.info("--------------------------------------------------------------------------------")
        if length > 0:
            log.info("Iterative populate: Last log run %s", str(last_log_run[0].created))
        else:
            log.info("Full populate: Can't find log of last run")
            iterative_populate = False
        log.info("--------------------------------------------------------------------------------")

    return iterative_populate, tstart, last_log_run


def more_options():
    """
    Appends common options to options list
    """

    option_list =  make_option('-f', '--force',
                               action='store_true',
                               dest='force',
                               default=False,
                               help='Forces a full populate for all students and rows, rather than iterative.')
    
    return option_list

        