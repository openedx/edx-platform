"""
API implementation of the Course Structure API for Python code.

Note: The course list and course detail functionality isn't currently supported here because
of the tricky interactions between DRF and the code.
Most of that information is available by accessing the course objects directly.
"""
from collections import OrderedDict
from .serializers import GradingPolicySerializer, CourseStructureSerializer
from .errors import CourseNotFoundError, CourseStructureNotAvailableError
from openedx.core.djangoapps.content.course_structures import models, tasks
from util.cache import cache
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


def course_structure(course_key, block_types=None):
    """
    Retrieves the entire course structure, including information about all the blocks used in the
    course if `block_types` is None else information about `block_types` will be returned only.
    Final serialized information will be cached.

    Args:
        course_key: the CourseKey of the course we'd like to retrieve.
        block_types: list of required block types. Possible values include sequential,
                     vertical, html, problem, video, and discussion. The type can also be
                     the name of a custom type of block used for the course.
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

    modified_timestamp = models.CourseStructure.objects.filter(course_id=course_key).values('modified')
    if modified_timestamp.exists():
        cache_key = 'openedx.content.course_structures.api.v0.api.course_structure.{}.{}.{}'.format(
            course_key, modified_timestamp[0]['modified'], '_'.join(block_types or [])
        )
        data = cache.get(cache_key)  # pylint: disable=maybe-no-member
        if data is not None:
            return data

        try:
            requested_course_structure = models.CourseStructure.objects.get(course_id=course.id)
        except models.CourseStructure.DoesNotExist:
            pass
        else:
            structure = requested_course_structure.structure
            if block_types is not None:
                blocks = requested_course_structure.ordered_blocks
                required_blocks = OrderedDict()
                for usage_id, block_data in blocks.iteritems():
                    if block_data['block_type'] in block_types:
                        required_blocks[usage_id] = block_data

                structure['blocks'] = required_blocks

            data = CourseStructureSerializer(structure).data
            cache.set(cache_key, data, None)  # pylint: disable=maybe-no-member
            return data

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
    return GradingPolicySerializer(course.raw_grader).data
