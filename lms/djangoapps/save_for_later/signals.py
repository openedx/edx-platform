"""
Signal handler for save for later
"""
from django.dispatch.dispatcher import receiver

from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_LMS_CRITICAL
from .models import SavedCourse, SavedProgram


@receiver(USER_RETIRE_LMS_CRITICAL)
def _listen_for_lms_retire(sender, **kwargs):  # pylint: disable=unused-argument
    user = kwargs.get('user')
    SavedCourse.delete_by_user_value(user.id, field='user_id')
    SavedProgram.delete_by_user_value(user.id, field='user_id')
