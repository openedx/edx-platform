"""
Handlers for student
"""
from django.conf import settings
from django.dispatch import receiver

from openedx_events.event_bus import get_producer
from openedx_events.learning.signals import (
    COURSE_UNENROLLMENT_COMPLETED,
)
from openedx.core.lib.events import determine_producer_config_for_signal_and_topic
import logging
log = logging.getLogger(__name__)


@receiver(COURSE_UNENROLLMENT_COMPLETED)
def course_unenrollment_receiver(sender, signal, **kwargs):
    """
    Removes user notification preference when user un-enrolls from the course
    """
    topic = getattr(settings, "EVENT_BUS_ENROLLMENT_LIFECYCLE_TOPIC", "course-unenrollment-lifecycle")
    producer_config_setting = determine_producer_config_for_signal_and_topic(COURSE_UNENROLLMENT_COMPLETED, topic)
    if producer_config_setting is True:
        log.info("Producing unenrollment-event event via config")
        return
    if settings.FEATURES.get("ENABLE_SEND_ENROLLMENT_EVENTS_OVER_BUS"):
        log.info("Producing unenrollment-event event via manual send")
        get_producer().send(
            signal=COURSE_UNENROLLMENT_COMPLETED,
            topic=topic,
            event_key_field='enrollment.course.course_key',
            event_data={'enrollment': kwargs.get('enrollment')},
            event_metadata=kwargs.get('metadata')
        )
