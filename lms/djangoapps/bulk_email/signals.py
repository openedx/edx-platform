"""
Signal handlers for the bulk_email app
"""


from django.dispatch import receiver

from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_MAILINGS
from common.djangoapps.student.models import CourseEnrollment

from .models import Optout


@receiver(USER_RETIRE_MAILINGS)
def force_optout_all(sender, **kwargs):
    """
    When a user is retired from all mailings this method will create an Optout
    row for any courses they may be enrolled in.
    """
    user = kwargs.get('user', None)

    if not user:
        raise TypeError('Expected a User type, but received None.')

    for enrollment in CourseEnrollment.objects.filter(user=user):
        Optout.objects.get_or_create(user=user, course_id=enrollment.course.id)
