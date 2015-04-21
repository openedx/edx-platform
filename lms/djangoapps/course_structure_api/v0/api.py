"""
API implementation of the Course Structure API for Python code.

Note: The course list and course detail functionality isn't currently supported here because of the tricky interactions between DRF and the code.
Most of that information is available by accessing the course objects directly.
"""

from course_structure_api.v0 import serializers
from course_structure_api.v0.errors import CourseNotFoundError, CourseStructureNotAvailableError
from openedx.core.djangoapps.content.course_structures import models, tasks
from courseware import courses


def _retrieve_course(course_key):
    """Retrieves the course for the given course key.

    Args:
        course_key: The CourseKey for the course we'd like to retrieve.
    Returns:
        the course that matches the CourseKey
    Raises:
        CourseNotFoundError

    """
    try:
        course = courses.get_course(course_key)
        return course
    except ValueError:
        raise CourseNotFoundError


def course_structure(course_key):
    """
    Retrieves the entire course structure, including information about all the blocks used in the course.

    Args:
        course_key: the CourseKey of the course we'd like to retrieve.
    Returns:
        The serialized output of the course structure:
            * root: The ID of the root node of the course structure.

            * blocks: A dictionary that maps block IDs to a collection of
            information about each block. Each block contains the following
            fields.

                * id: The ID of the block.

                * type: The type of block. Possible values include sequential,
                    vertical, html, problem, video, and discussion. The type can also be
                    the name of a custom type of block used for the course.

                * display_name: The display name configured for the block.

                * graded: Whether or not the sequential or problem is graded. The
                    value is true or false.

                * format: The assignment type.

                * children: If the block has child blocks, a list of IDs of the child
                blocks.
    Raises:
        CourseStructureNotAvailableError, CourseNotFoundError
    """
    course = _retrieve_course(course_key)
    try:
        course_structure = models.CourseStructure.objects.get(course_id=course.id)
        return serializers.CourseStructureSerializer(course_structure.structure).data
    except models.CourseStructure.DoesNotExist:
        # If we don't have data stored, generate it and return an error.
        tasks.update_course_structure.delay(unicode(course_key))
        raise CourseStructureNotAvailableError


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
    return serializers.GradingPolicySerializer(course.raw_grader).data
