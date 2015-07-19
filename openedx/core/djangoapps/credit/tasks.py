"""
This file contains celery tasks for credit course views.
"""

import datetime
from pytz import UTC

from django.conf import settings

from celery import task
from celery.utils.log import get_task_logger
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from .api import set_credit_requirements
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from openedx.core.djangoapps.credit.models import CreditCourse
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError

LOGGER = get_task_logger(__name__)


# XBlocks that can be added as credit requirements
CREDIT_REQUIREMENT_XBLOCK_CATEGORIES = [
    "edx-reverification-block",
]


# pylint: disable=not-callable
@task(default_retry_delay=settings.CREDIT_TASK_DEFAULT_RETRY_DELAY, max_retries=settings.CREDIT_TASK_MAX_RETRIES)
def update_credit_course_requirements(course_id):   # pylint: disable=invalid-name
    """
    Updates course requirements table for a course.

     Args:
        course_id(str): A string representation of course identifier

    Returns:
        None

    """
    try:
        course_key = CourseKey.from_string(course_id)
        is_credit_course = CreditCourse.is_credit_course(course_key)
        if is_credit_course:
            requirements = _get_course_credit_requirements(course_key)
            set_credit_requirements(course_key, requirements)
    except (InvalidKeyError, ItemNotFoundError, InvalidCreditRequirements) as exc:
        LOGGER.error('Error on adding the requirements for course %s - %s', course_id, unicode(exc))
        raise update_credit_course_requirements.retry(args=[course_id], exc=exc)
    else:
        LOGGER.info('Requirements added for course %s', course_id)


def _get_course_credit_requirements(course_key):
    """
    Returns the list of credit requirements for the given course.

    This will also call into the edx-proctoring subsystem to also
    produce proctored exam requirements for credit bearing courses

    It returns the minimum_grade_credit and also the ICRV checkpoints
    if any were added in the course

    Args:
        course_key (CourseKey): Identifier for the course.

    Returns:
        List of credit requirements (dictionaries)

    """
    credit_xblock_requirements = _get_credit_course_requirement_xblocks(course_key)
    min_grade_requirement = _get_min_grade_requirement(course_key)
    proctored_exams_requirements = _get_proctoring_requirements(course_key)
    credit_requirements = (
        min_grade_requirement + credit_xblock_requirements + proctored_exams_requirements
    )
    return credit_requirements


def _get_min_grade_requirement(course_key):
    """
    Get list of 'minimum_grade_credit' requirement for the given course.

    Args:
        course_key (CourseKey): Identifier for the course.

    Returns:
        The list of minimum_grade_credit requirements

    """
    course = modulestore().get_course(course_key, depth=0)
    try:
        return [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": getattr(course, "minimum_grade_credit")
                },
            }
        ]
    except AttributeError:
        LOGGER.error("The course %s does not has minimum_grade_credit attribute", unicode(course.id))
    else:
        return []


def _get_credit_course_requirement_xblocks(course_key):  # pylint: disable=invalid-name
    """Generate a course structure dictionary for the specified course.

    Args:
        course_key (CourseKey): Identifier for the course.

    Returns:
        The list of credit requirements xblocks dicts

    """
    requirements = []

    # Retrieve all XBlocks from the course that we know to be credit requirements.
    # For performance reasons, we look these up by their "category" to avoid
    # loading and searching the entire course tree.
    for category in CREDIT_REQUIREMENT_XBLOCK_CATEGORIES:
        requirements.extend([
            {
                "namespace": block.get_credit_requirement_namespace(),
                "name": block.get_credit_requirement_name(),
                "display_name": block.get_credit_requirement_display_name(),
                "criteria": {},
            }
            for block in _get_xblocks(course_key, category)
            if _is_credit_requirement(block)
        ])

    return requirements


def _is_in_course_tree(block):
    """
    Check that the XBlock is in the course tree.

    It's possible that the XBlock is not in the course tree
    if its parent has been deleted and is now an orphan.
    """
    ancestor = block.get_parent()
    while ancestor is not None and ancestor.location.category != "course":
        ancestor = ancestor.get_parent()

    return ancestor is not None


def _get_xblocks(course_key, category):
    """
    Retrieve all XBlocks in the course for a particular category.

    Returns only XBlocks that are published and haven't been deleted.
    """
    xblocks = [
        block for block in modulestore().get_items(
            course_key,
            qualifiers={"category": category},
            revision=ModuleStoreEnum.RevisionOption.published_only,
        )
        if _is_in_course_tree(block)
    ]

    # Secondary sort on credit requirement name
    xblocks = sorted(xblocks, key=lambda block: block.get_credit_requirement_display_name())

    # Primary sort on start date
    xblocks = sorted(xblocks, key=lambda block: (
        block.start if block.start is not None
        else datetime.datetime(datetime.MINYEAR, 1, 1).replace(tzinfo=UTC)
    ))

    return xblocks


def _is_credit_requirement(xblock):
    """
    Check if the given XBlock is a credit requirement.

    Args:
        xblock(XBlock): The given XBlock object

    Returns:
        True if XBlock is a credit requirement else False

    """
    required_methods = [
        "get_credit_requirement_namespace",
        "get_credit_requirement_name",
        "get_credit_requirement_display_name"
    ]

    for method_name in required_methods:
        if not callable(getattr(xblock, method_name, None)):
            LOGGER.error(
                "XBlock %s is marked as a credit requirement but does not "
                "implement %s", unicode(xblock), method_name
            )
            return False

    return True


def _get_proctoring_requirements(course_key):
    """
    Will return list of requirements regarding any exams that have been
    marked as proctored exams. For credit-bearing courses, all
    proctored exams must be validated and confirmed from a proctoring
    standpoint. The passing grade on an exam is not enough.

    Args:
        course_key: The key of the course in question

    Returns:
        list of requirements dictionary, one per active proctored exam

    """

    # Note: Need to import here as there appears to be
    # a circular reference happening when launching Studio
    # process
    from edx_proctoring.api import get_all_exams_for_course

    requirements = [
        {
            'namespace': 'proctored_exam',
            'name': 'proctored_exam_id:{id}'.format(id=exam['id']),
            'display_name': exam['exam_name'],
            'criteria': {},
        }
        for exam in get_all_exams_for_course(unicode(course_key))
        if exam['is_proctored'] and exam['is_active']
    ]

    log_msg = (
        'Registering the following as \'proctored_exam\' credit requirements: {log_msg}'.format(
            log_msg=requirements
        )
    )
    LOGGER.info(log_msg)

    return requirements
