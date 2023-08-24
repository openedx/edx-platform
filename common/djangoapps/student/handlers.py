"""
Handlers for student
"""
from django.conf import settings
from django.dispatch import receiver

from openedx_events.event_bus import get_producer
from openedx_events.learning.signals import (
    COURSE_UNENROLLMENT_COMPLETED,
)


@receiver(COURSE_UNENROLLMENT_COMPLETED)
def course_unenrollment_receiver(sender, signal, **kwargs):
    """
    Removes user notification preference when user un-enrolls from the course
    """
    if settings.FEATURES.get("ENABLE_SEND_ENROLLMENT_EVENTS_OVER_BUS"):
        get_producer().send(
            signal=COURSE_UNENROLLMENT_COMPLETED,
            topic=getattr(settings, "EVENT_BUS_ENROLLMENT_LIFECYCLE_TOPIC", "course-unenrollment-lifecycle"),
            event_key_field='enrollment.course.course_key',
            event_data={'enrollment': kwargs.get('enrollment')},
            event_metadata=kwargs.get('metadata')
        )
