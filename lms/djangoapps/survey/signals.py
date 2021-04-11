"""
Signal handlers for the survey app
"""


from django.dispatch.dispatcher import receiver

from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_LMS_MISC
from lms.djangoapps.survey.models import SurveyAnswer


@receiver(USER_RETIRE_LMS_MISC)
def _listen_for_lms_retire(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Listener for the USER_RETIRE_LMS_MISC signal, just does the SurveyAnswer retirement
    """
    user = kwargs.get('user')
    SurveyAnswer.retire_user(user.id)
