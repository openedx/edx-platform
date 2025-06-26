"""
Celery task for course date signals.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from edx_when.api import models as when_models
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.courses import get_course_assignments


User = get_user_model()


LOGGER = get_task_logger(__name__)


@shared_task
@set_code_owner_attribute
def update_assignment_dates_for_course(course_key_str):
    """
    Celery task to update assignment dates for a course.
    """
    try:
        LOGGER.info("Starting to update assignment dates for course %s", course_key_str)
        course_key = CourseKey.from_string(course_key_str)
        staff_user = User.objects.filter(is_staff=True).first()
        if not staff_user:
            LOGGER.error("No staff user found to update assignment dates for course %s", course_key_str)
            return
        assignments = get_course_assignments(course_key, staff_user)
        for assignment in assignments:
            LOGGER.info(
                "Updating assignment '%s' with due date '%s' for course %s",
                assignment.title,
                assignment.date,
                course_key_str
            )
            if not all((assignment.date, assignment.title)):
                LOGGER.warning(
                    "Skipping assignment '%s' for course %s because it has no date or title",
                    assignment,
                    course_key_str
                )
                continue
            when_models.ContentDate.objects.update_or_create(
                course_id=course_key,
                location=assignment.block_key,
                field='due',
                block_type=assignment.assignment_type,
                defaults={
                    'policy': when_models.DatePolicy.objects.get_or_create(abs_date=assignment.date)[0],
                    'assignment_title': assignment.title,
                    'course_name': course_key.course,
                    'subsection_name': assignment.title
                }
            )
        LOGGER.info("Successfully updated assignment dates for course %s", course_key_str)
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Could not update assignment dates for course %s", course_key_str)
        raise
