"""
This file contains celery tasks for credit views
"""

from celery.task import task
from celery.utils.log import get_task_logger
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from .api import set_credit_requirements
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from xmodule.modulestore.exceptions import ItemNotFoundError

LOGGER = get_task_logger(__name__)


@task()
def update_course_requirements(course_id):
    """ Updates course requirements table for course.

     Args:
        course_id(str): A string representation of course identifier

    Returns:
        None
    """
    try:
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)
        requirements = _get_course_credit_requirements(course)
        set_credit_requirements(course_key, requirements)
    except (InvalidKeyError, ItemNotFoundError, InvalidCreditRequirements) as exc:
        LOGGER.error('Error on adding the requirements for course %s - %s', course_id, unicode(exc))
    except Exception as exc:
        LOGGER.error('Error on adding the requirements for course %s - %s', course_id, unicode(exc))
    else:
        LOGGER.debug('Requirements added for course %s', course_id)


def _get_course_credit_requirements(course):
    icrv_requirements = _get_credit_course_requirements_xblocks(course)
    min_grade_requirement = _get_min_grade_requirement(course)
    icrv_requirements.extend(min_grade_requirement)
    return icrv_requirements


def _get_min_grade_requirement(course):
    requirement = [
        {
            "namespace": "grade",
            "name": "grade",
            "configuration": {
                "min_grade": get_min_grade_for_credit(course)
            }
        }
    ]
    return requirement


def _get_credit_course_requirements_xblocks(course):
    """ Generates a course structure dictionary for the specified course. """

    blocks_stack = [course]
    requirements_blocks = []
    while blocks_stack:
        curr_block = blocks_stack.pop()
        children = curr_block.get_children() if curr_block.has_children else []
        if _is_credit_requirement(curr_block):
            block = {
                "namespace": "reverification",
                "name": _get_block_name(curr_block),
                "configuration": ""
            }
            requirements_blocks.append(block)

        # Add this blocks children to the stack so that we can traverse them as well.
        blocks_stack.extend(children)
    return requirements_blocks


def get_min_grade_for_credit(course):
    """ This is a dummy function to continue work.
    """
    try:
        return course.min_grade
    except:  # pylint: disable=bare-except
        return 0.8


def _is_credit_requirement(xblock):
    try:
        return xblock.is_credit_requirement
    except:
        return False


def _get_block_name(xblock):
    try:
        return xblock.related_assessment
    except:
        return None
