""" This file contains celery tasks for credit course views """

from .api import set_credit_requirements
from celery.task import task
from celery.utils.log import get_task_logger
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


LOGGER = get_task_logger(__name__)


@task()
def update_course_requirements(course_id):
    """ Updates course requirements table for a course.

     Args:
        course_id(str): A string representation of course identifier

    Returns:
        None
    """
    try:
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "configuration": {
                    "min_grade": get_min_grade_for_credit(course)
                }
            }
        ]
        set_credit_requirements(course_key, requirements)
    except (InvalidKeyError, ItemNotFoundError, InvalidCreditRequirements) as exc:
        LOGGER.error('Error on adding the requirements for course %s - %s', course_id, unicode(exc))
    else:
        LOGGER.debug('Requirements added for course %s', course_id)


def get_min_grade_for_credit(course):
    """ This is a dummy function to continue work. """
    #  TODO: Remove this function before merging this PR
    try:
        return course.min_grade
    except:  # pylint: disable=bare-except
        return 0.8
