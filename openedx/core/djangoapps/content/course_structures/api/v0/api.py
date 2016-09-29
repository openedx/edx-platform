"""
API implementation of the Course Structure API for Python code.

Note: The course list and course detail functionality isn't currently supported here because
of the tricky interactions between DRF and the code.
Most of that information is available by accessing the course objects directly.

TODO: delete me once grading policy is implemented in course_api.
"""
from openedx.core.lib.exceptions import CourseNotFoundError
from .serializers import GradingPolicySerializer
from xmodule.modulestore.django import modulestore


def _retrieve_course(course_key):
    """Retrieves the course for the given course key.

    Args:
        course_key: The CourseKey for the course we'd like to retrieve.
    Returns:
        the course that matches the CourseKey
    Raises:
        CourseNotFoundError

    """
    course = modulestore().get_course(course_key, depth=0)
    if course is None:
        raise CourseNotFoundError

    return course


def course_grading_policy(course_key):
    """
    Retrieves the course grading policy.

    Args:
        course_key: CourseKey the corresponds to the course we'd like to know grading policy information about.
    Returns:
        The serialized version of the course grading policy containing the following information:
            * assignment_type: The type of the assignment, as configured by course
                staff. For example, course staff might make the assignment types Homework,
                Quiz, and Exam.

            * count: The number of assignments of the type.

            * dropped: Number of assignments of the type that are dropped.

            * weight: The weight, or effect, of the assignment type on the learner's
                final grade.
    """
    course = _retrieve_course(course_key)
    return GradingPolicySerializer(course.raw_grader, many=True).data
