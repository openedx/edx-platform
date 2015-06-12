"""
This file contains celery tasks for credit course views.
"""

from django.conf import settings

from celery import task
from celery.utils.log import get_task_logger
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from .api import set_credit_requirements
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from openedx.core.djangoapps.credit.models import CreditCourse
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

LOGGER = get_task_logger(__name__)


# pylint: disable=not-callable
@task(default_retry_delay=settings.CREDIT_TASK_DEFAULT_RETRY_DELAY, max_retries=settings.CREDIT_TASK_MAX_RETRIES)
def update_credit_course_requirements(course_id):   # pylint: disable=invalid-name
    """Updates course requirements table for a course.

     Args:
        course_id(str): A string representation of course identifier

    Returns:
        None

    """
    try:
        course_key = CourseKey.from_string(course_id)
        is_credit_course = CreditCourse.is_credit_course(course_key)
        if is_credit_course:
            course = modulestore().get_course(course_key)
            requirements = _get_course_credit_requirements(course)
            set_credit_requirements(course_key, requirements)
    except (InvalidKeyError, ItemNotFoundError, InvalidCreditRequirements) as exc:
        LOGGER.error('Error on adding the requirements for course %s - %s', course_id, unicode(exc))
        raise update_credit_course_requirements.retry(args=[course_id], exc=exc)
    else:
        LOGGER.info('Requirements added for course %s', course_id)


def _get_course_credit_requirements(course):
    """Returns the list of credit requirements for the given course.

    It returns the minimum_grade_credit and also the ICRV checkpoints
    if any were added in the course

    Args:
        course(Course): The course object

    Returns:
        List of minimum_grade_credit and ICRV requirements

    """
    credit_xblock_requirements = _get_credit_course_requirement_xblocks(course)
    min_grade_requirement = _get_min_grade_requirement(course)
    credit_requirements = credit_xblock_requirements + min_grade_requirement
    return credit_requirements


def _get_min_grade_requirement(course):
    """Get list of 'minimum_grade_credit' requirement for the given course.

    Args:
        course(Course): The course object

    Raises:
        AttributeError if the course has not 'minimum_grade_credit' attribute

    Returns:
        The list of minimum_grade_credit requirements

    """
    requirement = []
    try:
        requirement = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": getattr(course, "minimum_grade_credit")
                }
            }
        ]
    except AttributeError:
        LOGGER.error("The course %s does not has minimum_grade_credit attribute", unicode(course.id))
    return requirement


def _get_credit_course_requirement_xblocks(course):  # pylint: disable=invalid-name
    """Generate a course structure dictionary for the specified course.

    Args:
        course(Course): The course object

    Returns:
        The list of credit requirements xblocks dicts

    """
    blocks_stack = [course]
    requirements_blocks = []
    while blocks_stack:
        curr_block = blocks_stack.pop()
        children = curr_block.get_children() if curr_block.has_children else []
        if _is_credit_requirement(curr_block):
            block = {
                "namespace": curr_block.get_credit_requirement_namespace(),
                "name": curr_block.get_credit_requirement_name(),
                "display_name": curr_block.get_credit_requirement_display_name(),
                "criteria": ""
            }
            requirements_blocks.append(block)

        # Add the children of current block to the stack so that we can
        # traverse them as well.
        blocks_stack.extend(children)
    return requirements_blocks


def _is_credit_requirement(xblock):
    """Check if the given XBlock is a credit requirement.

    Args:
        xblock(XBlock): The given XBlock object

    Returns:
        True if XBlock is a credit requirement else False

    """
    is_credit_requirement = False

    if callable(getattr(xblock, "is_course_credit_requirement", None)):
        is_credit_requirement = xblock.is_course_credit_requirement()
        if is_credit_requirement:
            if not callable(getattr(xblock, "get_credit_requirement_namespace", None)):
                is_credit_requirement = False
                LOGGER.error(
                    "XBlock %s is marked as a credit requirement but does not "
                    "implement get_credit_requirement_namespace()", unicode(xblock)
                )
            if not callable(getattr(xblock, "get_credit_requirement_name", None)):
                is_credit_requirement = False
                LOGGER.error(
                    "XBlock %s is marked as a credit requirement but does not "
                    "implement get_credit_requirement_name()", unicode(xblock)
                )
    return is_credit_requirement
