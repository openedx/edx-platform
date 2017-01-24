"""
This file contains celery tasks for credit course views.
"""

from celery import task
from celery.utils.log import get_task_logger
from django.conf import settings
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx.core.djangoapps.credit.api import set_credit_requirements
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.utils import get_course_blocks
from xmodule.modulestore.django import modulestore
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
    block_requirements = credit_xblock_requirements + proctored_exams_requirements
    # sort credit requirements list based on start date and put all the
    # requirements with no start date at the end of requirement list.
    sorted_block_requirements = sorted(
        block_requirements, key=lambda x: (x['start_date'] is None, x['start_date'], x['display_name'])
    )

    credit_requirements = (
        min_grade_requirement + sorted_block_requirements
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
                "display_name": "Minimum Grade",
                "criteria": {
                    "min_grade": course.minimum_grade_credit
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
                'start_date': block.start,
                "criteria": {},
            }
            for block in _get_xblocks(course_key, category)
            if _is_credit_requirement(block)
        ])

    return requirements


def _get_xblocks(course_key, category):
    """
    Retrieve all XBlocks in the course for a particular category.

    Returns only XBlocks that are published and haven't been deleted.
    """
    xblocks = get_course_blocks(course_key, category)

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

    requirements = []
    for exam in get_all_exams_for_course(unicode(course_key)):
        if exam['is_proctored'] and exam['is_active'] and not exam['is_practice_exam']:
            try:
                usage_key = UsageKey.from_string(exam['content_id'])
                proctor_block = modulestore().get_item(usage_key)
            except (InvalidKeyError, ItemNotFoundError):
                LOGGER.info("Invalid content_id '%s' for proctored block '%s'", exam['content_id'], exam['exam_name'])
                proctor_block = None

            if proctor_block:
                requirements.append(
                    {
                        'namespace': 'proctored_exam',
                        'name': exam['content_id'],
                        'display_name': exam['exam_name'],
                        'start_date': proctor_block.start if proctor_block.start else None,
                        'criteria': {},
                    })

    if requirements:
        log_msg = (
            'Registering the following as \'proctored_exam\' credit requirements: {log_msg}'.format(
                log_msg=requirements
            )
        )
        LOGGER.info(log_msg)

    return requirements
