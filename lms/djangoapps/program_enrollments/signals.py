"""
Signal handlers for program enrollments
"""
from __future__ import absolute_import

from django.dispatch.dispatcher import receiver

from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_LMS_MISC
from lms.djangoapps.program_enrollments.models import ProgramEnrollment


@receiver(USER_RETIRE_LMS_MISC)
def _listen_for_lms_retire(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Listener for the USER_RETIRE_LMS_MISC signal, does user retirement
    """
    user = kwargs.get('user')
    ProgramEnrollment.retire_user(user.id)
