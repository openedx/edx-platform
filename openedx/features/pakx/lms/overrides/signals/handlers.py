"""
Progress Email related signal handlers.
"""

from logging import getLogger
from django.dispatch import receiver

from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE
from openedx.features.pakx.lms.overrides.tasks import add_enrollment_record, remove_enrollment_record


@receiver(ENROLL_STATUS_CHANGE)
def copy_active_course_enrollment(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Awards enrollment badge to the given user on new enrollments.
    """

    course_key = str(kwargs.get('course_id', "Null"))
    if event == EnrollStatusChange.enroll:
        add_enrollment_record.delay(user.username, user.email, course_key)
    elif event == EnrollStatusChange.unenroll:
        remove_enrollment_record.delay(user.username, user.email, course_key)
