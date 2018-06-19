"""
Signal handlers for the survey app
"""
from django.dispatch.dispatcher import receiver

from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_LMS_MISC

from survey.models import SurveyAnswer


@receiver(USER_RETIRE_LMS_MISC)
def _listen_for_lms_retire(sender, **kwargs):  # pylint: disable=unused-argument
    user = kwargs.get('user')
    SurveyAnswer.retire_user(user.id)
