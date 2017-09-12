"""
This module contains all general use or cross-use handlers.
"""
import logging

from django.dispatch import receiver

from certificates.models import CertificateGenerationCourseSetting
from signals import COURSE_PACING_CHANGED

log = logging.getLogger(__name__)


@receiver(COURSE_PACING_CHANGED, dispatch_uid="update_cert_settings_on_pacing_change")
def _update_cert_settings_on_pacing_change(sender, updated_course_overview, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that course pacing has changed and enable/disable
    the self-generated certificates according to course-pacing.
    """
    toggle_self_generated_certs(updated_course_overview.id, updated_course_overview.self_paced)
    log.info(u'Certificate Generation Setting Toggled for {course_id} via pacing change'.format(
        course_id=updated_course_overview.id
    ))


def toggle_self_generated_certs(course_key, course_self_paced):
    """
    Enable or disable self-generated certificates for a course according to pacing.
    """
    CertificateGenerationCourseSetting.set_self_generatation_enabled_for_course(course_key, course_self_paced)
