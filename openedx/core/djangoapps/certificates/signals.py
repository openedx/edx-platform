import logging
from django.dispatch.dispatcher import receiver
from openedx.core.djangoapps.content.course_overviews.signals import COURSE_PACING_CHANGED

log = logging.getLogger(__name__)

@receiver(COURSE_PACING_CHANGED, dispatch_uid="update_cert_settings_on_pacing_change")
def _update_cert_settings_on_pacing_change(sender, updated_course_overview, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that course pacing has changed and enable/disable
    the self-generated certificates according to course-pacing.
    """
    log.info('This reciever will now work')