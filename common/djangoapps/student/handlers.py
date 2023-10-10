"""
Handlers for student
"""
from django.conf import settings
from django.dispatch import receiver
from edx_django_utils.monitoring import set_custom_attribute

from openedx_events.event_bus import get_producer
from openedx_events.learning.signals import (
    COURSE_UNENROLLMENT_COMPLETED,
)
import logging
log = logging.getLogger(__name__)


def _determine_producer_config_for_signal_and_topic(signal, topic):
    """
    Utility method to determine the setting for the given signal and topic in EVENT_BUS_PRODUCER_CONFIG

    Records to New Relic for later analysis.

    Parameters
        signal (OpenEdxPublicSignal): The signal being sent to the event bus
        topic (string): The topic to which the signal is being sent

    Returns
        True if the signal is enabled for that topic in EVENT_BUS_PRODUCER_CONFIG
        False if the signal is explicitly disabled for that topic in EVENT_BUS_PRODUCER_CONFIG
        None if the signal/topic pair is not present in EVENT_BUS_PRODUCER_CONFIG
    """
    event_type_producer_configs = getattr(settings, "EVENT_BUS_PRODUCER_CONFIG",
                                          {}).get(signal.event_type, {})
    topic_config = event_type_producer_configs.get(topic, {})
    topic_setting = topic_config.get('enabled', None)
    if topic_setting is True:
        set_custom_attribute('producer_config_setting', 'True')
        return
    if topic_setting is False:
        set_custom_attribute('producer_config_setting', 'False')
    if topic_setting is None:
        set_custom_attribute('producer_config_setting', 'Unset')
    return topic_setting


@receiver(COURSE_UNENROLLMENT_COMPLETED)
def course_unenrollment_receiver(sender, signal, **kwargs):
    """
    Removes user notification preference when user un-enrolls from the course
    """
    topic = getattr(settings, "EVENT_BUS_ENROLLMENT_LIFECYCLE_TOPIC", "course-unenrollment-lifecycle")
    producer_config_setting = _determine_producer_config_for_signal_and_topic(COURSE_UNENROLLMENT_COMPLETED, topic)
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
