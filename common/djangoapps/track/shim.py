"""Map new event context values to old top-level field values. Ensures events can be parsed by legacy parsers."""

import json
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey


log = logging.getLogger(__name__)

CONTEXT_FIELDS_TO_INCLUDE = [
    'username',
    'session',
    'ip',
    'agent',
    'host',
    'referer',
    'accept_language'
]


class LegacyFieldMappingProcessor(object):
    """Ensures all required fields are included in emitted events"""

    def __call__(self, event):
        context = event.get('context', {})
        if 'context' in event:
            for field in CONTEXT_FIELDS_TO_INCLUDE:
                self.move_from_context(field, event)
            remove_shim_context(event)

        if 'data' in event:
            if context.get('event_source', '') == 'browser' and isinstance(event['data'], dict):
                event['event'] = json.dumps(event['data'])
            else:
                event['event'] = event['data']
            del event['data']
        else:
            event['event'] = {}

        if 'timestamp' in context:
            event['time'] = context['timestamp']
            del context['timestamp']
        elif 'timestamp' in event:
            event['time'] = event['timestamp']

        if 'timestamp' in event:
            del event['timestamp']

        self.move_from_context('event_type', event, event.get('name', ''))
        self.move_from_context('event_source', event, 'server')
        self.move_from_context('page', event, None)

    def move_from_context(self, field, event, default_value=''):
        """Move a field from the context to the top level of the event."""
        context = event.get('context', {})
        if field in context:
            event[field] = context[field]
            del context[field]
        else:
            event[field] = default_value


def remove_shim_context(event):
    if 'context' in event:
        context = event['context']
        # These fields are present elsewhere in the event at this point
        context_fields_to_remove = set(CONTEXT_FIELDS_TO_INCLUDE)
        # This field is only used for Segment web analytics and does not concern researchers
        context_fields_to_remove.add('client_id')
        for field in context_fields_to_remove:
            if field in context:
                del context[field]


NAME_TO_EVENT_TYPE_MAP = {
    'edx.video.played': 'play_video',
    'edx.video.paused': 'pause_video',
    'edx.video.stopped': 'stop_video',
    'edx.video.loaded': 'load_video',
    'edx.video.position.changed': 'seek_video',
    'edx.video.seeked': 'seek_video',
    'edx.video.transcript.shown': 'show_transcript',
    'edx.video.transcript.hidden': 'hide_transcript',
}


class VideoEventProcessor(object):
    """
    Converts new format video events into the legacy video event format.

    Mobile devices cannot actually emit events that exactly match their counterparts emitted by the LMS javascript
    video player. Instead of attempting to get them to do that, we instead insert a shim here that converts the events
    they *can* easily emit and converts them into the legacy format.

    TODO: Remove this shim and perform the conversion as part of some batch canonicalization process.

    """

    def __call__(self, event):
        name = event.get('name')
        if not name:
            return

        if name not in NAME_TO_EVENT_TYPE_MAP:
            return

        # Convert edx.video.seeked to edx.video.position.changed because edx.video.seeked was not intended to actually
        # ever be emitted.
        if name == "edx.video.seeked":
            event['name'] = "edx.video.position.changed"

        event['event_type'] = NAME_TO_EVENT_TYPE_MAP[name]

        if 'event' not in event:
            return
        payload = event['event']

        if 'module_id' in payload:
            module_id = payload['module_id']
            try:
                usage_key = UsageKey.from_string(module_id)
            except InvalidKeyError:
                log.warning('Unable to parse module_id "%s"', module_id, exc_info=True)
            else:
                payload['id'] = usage_key.html_id()

            del payload['module_id']

        if 'current_time' in payload:
            payload['currentTime'] = payload.pop('current_time')

        if 'context' in event:
            context = event['context']

            # Converts seek_type to seek and skip|slide to onSlideSeek|onSkipSeek
            if 'seek_type' in payload:
                seek_type = payload['seek_type']
                if seek_type == 'slide':
                    payload['type'] = "onSlideSeek"
                elif seek_type == 'skip':
                    payload['type'] = "onSkipSeek"
                del payload['seek_type']

            # For the iOS build that is returning a +30 for back skip 30
            if (
                context['application']['version'] == "1.0.02" and
                context['application']['name'] == "edx.mobileapp.iOS"
            ):
                if 'requested_skip_interval' in payload and 'type' in payload:
                    if (
                        payload['requested_skip_interval'] == 30 and
                        payload['type'] == "onSkipSeek"
                    ):
                        payload['requested_skip_interval'] = -30

            # For the Android build that isn't distinguishing between skip/seek
            if 'requested_skip_interval' in payload:
                if abs(payload['requested_skip_interval']) != 30:
                    if 'type' in payload:
                        payload['type'] = 'onSlideSeek'

            if 'open_in_browser_url' in context:
                page, _sep, _tail = context.pop('open_in_browser_url').rpartition('/')
                event['page'] = page

        event['event'] = json.dumps(payload)


class GoogleAnalyticsProcessor(object):
    """Adds course_id as label, and sets nonInteraction property"""

    # documentation of fields here: https://segment.com/docs/integrations/google-analytics/
    # this should *only* be used on events destined for segment.com and eventually google analytics
    def __call__(self, event):
        context = event.get('context', {})
        course_id = context.get('course_id')

        if course_id is not None:
            event['label'] = course_id

        event['nonInteraction'] = 1
