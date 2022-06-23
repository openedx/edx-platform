"""Map new event context values to old top-level field values. Ensures events can be parsed by legacy parsers."""


import json
import logging
import uuid
import copy

import analytics
from analytics.client import Client
from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers
from openedx.core.djangoapps.appsembler.eventtracking import exceptions, utils

from .transformers import EventTransformerRegistry

CONTEXT_FIELDS_TO_INCLUDE = [
    'username',
    'session',
    'ip',
    'agent',
    'host',
    'referer',
    'accept_language'
]

logger = logging.getLogger(__name__)


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
    """
    Remove obsolete fields from event context.
    """
    if 'context' in event:
        context = event['context']
        # These fields are present elsewhere in the event at this point
        context_fields_to_remove = set(CONTEXT_FIELDS_TO_INCLUDE)
        # This field is only used for Segment web analytics and does not concern researchers
        context_fields_to_remove.add('client_id')
        for field in context_fields_to_remove:
            if field in context:
                del context[field]


class GoogleAnalyticsProcessor(object):
    """Adds course_id as label, and sets nonInteraction property"""

    # documentation of fields here: https://segment.com/docs/integrations/google-analytics/
    # this should *only* be used on events destined for segment.com and eventually google analytics
    def __call__(self, event):
        context = event.get('context', {})
        course_id = context.get('course_id')

        copied_event = event.copy()
        if course_id is not None:
            copied_event['label'] = course_id

        copied_event['nonInteraction'] = 1

        return copied_event


class PrefixedEventProcessor(object):
    """
    Process any events whose name or prefix (ending with a '.') is registered
    as an EventTransformer.
    """

    def __call__(self, event):
        """
        If the event is registered with the EventTransformerRegistry, transform
        it.  Otherwise do nothing to it, and continue processing.
        """
        try:
            event = EventTransformerRegistry.create_transformer(event)
        except KeyError:
            return
        event.transform()
        return event


def is_celery_worker():
    """
    Check if this execution is for celery of not. If the result is <False>; it's not guaranteed that the execution is
    not for Celery. Because the method returns <False> if <IS_CELERY_WORKER> attribute is missing in settings

    <IS_CELERY_WORKER> value is set during deployment using <celery_worker> variable in <edxapp> role

    :return: <True> if the execution is for Celery; and <False> otherwise
    """
    return getattr(settings, 'IS_CELERY_WORKER', False) or False


class DefaultMultipleSegmentClient(object):
    """
    Proxy client to call original segment account and site account
    """

    def __init__(self):
        self._main_client = self._create_client(analytics.write_key)

    def _create_client(self, write_key):
        params = {'sync_mode': is_celery_worker()}
        for param in ['host', 'debug', 'on_error', 'send']:
            if hasattr(analytics, param):
                params[param] = getattr(analytics, param)
        return Client(write_key, **params)

    def _get_site_segment_key(self, *args):
        """
        Find the Site-specific Segment writekey by possible strategies.
        """

        site_segment_key = None
        try:
            # this code should only ever run on TRACK events which
            # will pass args like (user_id, event name, event dict)
            event_props = args[2]
            siteconfig = utils.get_site_config_for_event(event_props)
            if siteconfig:
                site_segment_key = siteconfig.get_secret_value('SEGMENT_KEY')
        except (IndexError, exceptions.EventProcessingError):
            try:
                event_name = args[1]
            except IndexError:
                event_name = '(unknown event name)'
            logger.warning(
                "Error retrieving Site SEGMENT_KEY. Cannot send event %s to "
                "Site's Segment account. Sending only to main Segment client. "
                "Error was: ", event_name, exc_info=True
            )
        return site_segment_key

    def __getattr__(self, name, *args, **kwargs):

        def proxy(*args, **kwargs):
            result = getattr(self._main_client, name)(*args, **kwargs)

            site_client = None

            site_segment_key = self._get_site_segment_key(*args)
            if site_segment_key:
                site_client = self._create_client(site_segment_key)

            if not site_client:
                return result

            # Replace the message id with a new one if it was set.
            if 'message_id' in kwargs:
                kwargs['message_id'] = uuid.uuid4().hex

            # Use site GATI instead of main GATI if it was set.
            if kwargs.get('context', {}).get('Google Analytics', None):
                gati = helpers.get_value('GOOGLE_ANALYTICS_TRACKING_ID')
                kwargs['context'] = copy.deepcopy(kwargs['context'] or {})
                if gati:
                    kwargs['context']['Google Analytics']['clientId'] = gati
                else:
                    kwargs['context'].pop('Google Analytics', None)

            getattr(site_client, name)(*args, **kwargs)
            return result

        return proxy
