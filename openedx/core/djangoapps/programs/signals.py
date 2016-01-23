"""
This module contains signals / handlers related to programs.
"""
import logging

from django.dispatch import receiver

from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED
from openedx.core.djangoapps.programs.models import ProgramsApiConfig


LOGGER = logging.getLogger(__name__)


@receiver(COURSE_CERT_AWARDED)
def handle_course_cert_awarded(sender, user, course_key, mode, status, **kwargs):  # pylint: disable=unused-argument
    """
    If programs is enabled and a learner is awarded a course certificate,
    schedule a celery task to process any programs certificates for which
    the learner may now be eligible.

    Args:
        sender:
            class of the object instance that sent this signal
        user:
            django.contrib.auth.User - the user to whom a cert was awarded
        course_key:
            refers to the course run for which the cert was awarded
        mode:
            mode / certificate type, e.g. "verified"
        status:
            either "downloadable" or "generating"

    Returns:
        None

    """
    if not ProgramsApiConfig.current().is_certification_enabled:
        return

    # schedule background task to process
    LOGGER.debug(
        'handling COURSE_CERT_AWARDED: username=%s, course_key=%s, mode=%s, status=%s',
        user,
        course_key,
        mode,
        status,
    )
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from openedx.core.djangoapps.programs import tasks
    tasks.award_program_certificates.delay(user.username)
