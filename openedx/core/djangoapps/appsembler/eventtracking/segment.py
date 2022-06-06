"""
Custom event processors and other functionality for the Segment backend.
"""

from django.conf import settings

from openedx.core.djangoapps.appsembler.eventtracking.utils import (
    get_site_config_for_event
)
from openedx.core.djangoapps.appsembler.eventtracking.exceptions import (
    EventProcessingError
)


def fix_user_id(event):
    """
    Adds <user_id> from top level of <event> into <event['context']>

    :param event: event dictionary to be processes
    :return: dictionary (the changed event)
    """
    context = event.get('context')
    if context is None:
        return event

    if context.get('user_id') is not None:
        return event

    context['user_id'] = event.get('user_id')
    return event


class SegmentTopLevelPropertiesProcessor(object):
    """

    Most Segment.io Destination APIs require properties to be at the top level
    of the event. Copy all properties contained within the event's 'data' key
    to the top level of the event dict.

    We copy properties instead of reassign to not break previous integrations.

    For example: by default, tracker.emit() will produce an event
    with most interesting properties in the `data` key, like:

    analytics.track('13', 'edx.bi.completion.user.chapter.started', {
    'context': { ... },
    'data': {
        'block_id': 'block-v1:foo+101+forever+type@chapter+block@3707382f0c284b6aadbd7c50d767ca8f',
        'block_name': 'Section 1',
        'completion_percent': 33.3333333333333,
        'course_id': 'course-v1:foo+101+forever',
        'course_name': 'CompletionTest',
        'label': 'chapter Section 1 started'
    },
    'name': 'edx.bi.completion.user.chapter.started',
    ...
    })

    Many/most Segment Destinations will not be able to access properties inside 'data'.
    Copy these to the top level of the event before emitting.
    For example, the previous becomes:
    analytics.track('13', 'edx.bi.completion.user.chapter.started', {
    'context': { ... },
    'block_id': 'block-v1:foo+101+forever+type@chapter+block@3707382f0c284b6aadbd7c50d767ca8f',
    'block_name': 'Section 1',
    'completion_percent': 33.3333333333333,
    'course_id': 'course-v1:foo+101+forever',
    'course_name': 'CompletionTest',
    'label': 'chapter Section 1 started',
    'data': {
        'block_id': 'block-v1:foo+101+forever+type@chapter+block@3707382f0c284b6aadbd7c50d767ca8f',
        'block_name': 'Section 1',
        'completion_percent': 33.3333333333333,
        'course_id': 'course-v1:foo+101+forever',
        'course_name': 'CompletionTest',
        'label': 'chapter Section 1 started'
    },
    'name': 'edx.bi.completion.user.chapter.started',
    ...
    })


    Always returns the event for continued processing.
    """
    def __call__(self, event):
        """
        Process only if processor is enabled for Site.
        """
        try:
            siteconfig = get_site_config_for_event(event['data'])
            if not siteconfig.get_value(
                'COPY_SEGMENT_EVENT_PROPERTIES_TO_TOP_LEVEL',
                settings.COPY_SEGMENT_EVENT_PROPERTIES_TO_TOP_LEVEL
            ):
                return event
        except (AttributeError, EventProcessingError):
            return event

        try:
            for key, val in event['data'].items():
                if key in event:
                    try:
                        event[key].update(event['data'][key])  # dict
                    except AttributeError:
                        try:
                            event[key].extend(event['data'][key])  # list
                        except AttributeError:
                            event[key] = val
                else:
                    event[key] = val
        except (KeyError, AttributeError):  # no 'data' or no sub-properties
            pass

        event = fix_user_id(event=event)

        return event
