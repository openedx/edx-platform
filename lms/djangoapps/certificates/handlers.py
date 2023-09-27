"""
Handlers for credits
"""
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from openedx_events.learning.signals import EXAM_ATTEMPT_REJECTED

from lms.djangoapps.certificates.services import CertificateService

User = get_user_model()

log = logging.getLogger(__name__)




@receiver(EXAM_ATTEMPT_REJECTED)
def handle_exam_attempt_rejected_event(sender, signal, **kwargs):
    """
    Consume `EXAM_ATTEMPT_REJECTED` events from the event bus.
    Pass the received data to invalidate_certificate in the services.py file in this folder.
    """
    event_data = kwargs.get('exam_attempt')
    user_data = event_data.student_user
    usage_key = event_data.usage_key

    # Note that the usage_key is the same as the course_key, and is being passed in as the course_key param
    CertificateService.invalidate_certificate(user_id=user_data.id, course_key_or_id=usage_key)
