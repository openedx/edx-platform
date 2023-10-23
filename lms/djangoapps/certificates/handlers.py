"""
Handlers for credits
"""
import logging

from django.contrib.auth import get_user_model
from django.dispatch import receiver
from openedx_events.learning.signals import EXAM_ATTEMPT_REJECTED

from lms.djangoapps.certificates.api import invalidate_certificate

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
    course_key = event_data.course_key

    # Note that the course_key is the same as the course_key_or_id, and is being passed in as the course_key param
    invalidate_certificate(user_data.id, course_key, source='exam_event')
