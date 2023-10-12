"""Temporary method for use in rolling out a new event producer configuration."""

from django.conf import settings
from edx_django_utils.monitoring import set_custom_attribute


def determine_producer_config_for_signal_and_topic(signal, topic):
    """
    Utility method to determine the setting for the given signal and topic in EVENT_BUS_PRODUCER_CONFIG

    Records to New Relic for later analysis.

    Parameters
        signal (OpenEdxPublicSignal): The signal being sent to the event bus
        topic (string): The topic to which the signal is being sent (without environment prefix)

    Returns
        True if the signal is enabled for that topic in EVENT_BUS_PRODUCER_CONFIG
        False if the signal is explicitly disabled for that topic in EVENT_BUS_PRODUCER_CONFIG
        None if the signal/topic pair is not present in EVENT_BUS_PRODUCER_CONFIG
    """
    event_type_producer_configs = getattr(settings, "EVENT_BUS_PRODUCER_CONFIG",
                                          {}).get(signal.event_type, {})
    topic_config = event_type_producer_configs.get(topic, {})
    topic_setting = topic_config.get('enabled', None)
    set_custom_attribute(f'producer_config_setting_{topic}_{signal.event_type}',
                         topic_setting if topic_setting is not None else 'Unset')
    return topic_setting
