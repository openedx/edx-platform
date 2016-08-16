"""
Functionality for course-level grades.
"""
from collections import namedtuple
from logging import getLogger

import dogstats_wrapper as dog_stats_api

from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_by_id
from .new.course_grade import CourseGradeFactory


log = getLogger(__name__)


GradeResult = namedtuple('StudentGrade', ['student', 'gradeset', 'err_msg'])


def iterate_grades_for(course_or_id, students):
    """
    Given a course_id and an iterable of students (User), yield a GradeResult
    for every student enrolled in the course.  GradeResult is a named tuple of:

    (student, gradeset, err_msg)

    If an error occurred, gradeset will be an empty dict and err_msg will be an
    exception message. If there was no error, err_msg is an empty string.

    The gradeset is a dictionary with the following fields:

    - grade : A final letter grade.
    - percent : The final percent for the class (rounded up).
        - section_breakdown : A breakdown of each section that makes
        up the grade. (For display)
    - grade_breakdown : A breakdown of the major components that
        make up the final grade. (For display)
    - raw_scores: contains scores for every graded module
    """
    if isinstance(course_or_id, (basestring, CourseKey)):
        course = get_course_by_id(course_or_id)
    else:
        course = course_or_id

    for student in students:
        with dog_stats_api.timer('lms.grades.iterate_grades_for', tags=[u'action:{}'.format(course.id)]):
            try:
                gradeset = summary(student, course)
                yield GradeResult(student, gradeset, "")
            except Exception as exc:  # pylint: disable=broad-except
                # Keep marching on even if this student couldn't be graded for
                # some reason, but log it for future reference.
                log.exception(
                    'Cannot grade student %s (%s) in course %s because of exception: %s',
                    student.username,
                    student.id,
                    course.id,
                    exc.message
                )
                yield GradeResult(student, {}, exc.message)


def summary(student, course):
    """
    Returns the grade summary of the student for the given course.

    Also sends a signal to update the minimum grade requirement status.
    """
    return CourseGradeFactory(student).create(course).summary
