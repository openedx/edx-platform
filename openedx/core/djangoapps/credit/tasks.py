""" This file contains celery tasks for credit course views """

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
def update_course_requirements(course_id):
    """ Updates course requirements table for a course.

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
            requirements = [
                {
                    "namespace": "grade",
                    "name": "grade",
                    "criteria": {
                        "min_grade": get_min_grade_for_credit(course)
                    }
                }
            ]
            set_credit_requirements(course_key, requirements)
    except (InvalidKeyError, ItemNotFoundError, InvalidCreditRequirements) as exc:
        LOGGER.error('Error on adding the requirements for course %s - %s', course_id, unicode(exc))
        raise update_course_requirements.retry(args=[course_id], exc=exc)
    else:
        LOGGER.info('Requirements added for course %s', course_id)


def get_min_grade_for_credit(course):
    """ Returns the min_grade for the credit requirements """
    return getattr(course, "min_grade", 0.8)
