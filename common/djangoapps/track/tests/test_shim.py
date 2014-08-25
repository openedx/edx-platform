"""Ensure emitted events contain the fields legacy processors expect to find."""

from datetime import datetime

from freezegun import freeze_time
from mock import sentinel
from django.test import TestCase
from django.test.utils import override_settings
from pytz import UTC

from eventtracking.django import DjangoTracker


IN_MEMORY_BACKEND = {
    'mem': {
        'ENGINE': 'track.tests.test_shim.InMemoryBackend'
    }
}

LEGACY_SHIM_PROCESSOR = [
    {
        'ENGINE': 'track.shim.LegacyFieldMappingProcessor'
    }
]

FROZEN_TIME = datetime(2013, 10, 3, 8, 24, 55, tzinfo=UTC)


@freeze_time(FROZEN_TIME)
class LegacyFieldMappingProcessorTestCase(TestCase):
    """Ensure emitted events contain the fields legacy processors expect to find."""

    @override_settings(
        EVENT_TRACKING_BACKENDS=IN_MEMORY_BACKEND,
        EVENT_TRACKING_PROCESSORS=LEGACY_SHIM_PROCESSOR,
    )
    def test_event_field_mapping(self):
        django_tracker = DjangoTracker()

        data = {sentinel.key: sentinel.value}

        context = {
            'username': sentinel.username,
            'session': sentinel.session,
            'ip': sentinel.ip,
            'host': sentinel.host,
            'agent': sentinel.agent,
            'path': sentinel.path,
            'user_id': sentinel.user_id,
            'course_id': sentinel.course_id,
            'org_id': sentinel.org_id,
            'event_type': sentinel.event_type,
            'client_id': sentinel.client_id,
        }
        with django_tracker.context('test', context):
            django_tracker.emit(sentinel.name, data)

        emitted_event = django_tracker.backends['mem'].get_event()

        expected_event = {
            'event_type': sentinel.event_type,
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                'course_id': sentinel.course_id,
                'org_id': sentinel.org_id,
                'path': sentinel.path,
            },
            'event': data,
            'username': sentinel.username,
            'event_source': 'server',
            'time': FROZEN_TIME,
            'agent': sentinel.agent,
            'host': sentinel.host,
            'ip': sentinel.ip,
            'page': None,
            'session': sentinel.session,
        }
        self.assertEqual(expected_event, emitted_event)

    @override_settings(
        EVENT_TRACKING_BACKENDS=IN_MEMORY_BACKEND,
        EVENT_TRACKING_PROCESSORS=LEGACY_SHIM_PROCESSOR,
    )
    def test_missing_fields(self):
        django_tracker = DjangoTracker()

        django_tracker.emit(sentinel.name)

        emitted_event = django_tracker.backends['mem'].get_event()

        expected_event = {
            'event_type': sentinel.name,
            'name': sentinel.name,
            'context': {},
            'event': {},
            'username': '',
            'event_source': 'server',
            'time': FROZEN_TIME,
            'agent': '',
            'host': '',
            'ip': '',
            'page': None,
            'session': '',
        }
        self.assertEqual(expected_event, emitted_event)


class InMemoryBackend(object):
    """A backend that simply stores all events in memory"""

    def __init__(self):
        super(InMemoryBackend, self).__init__()
        self.events = []

    def send(self, event):
        """Store the event in a list"""
        self.events.append(event)

    def get_event(self):
        """Return the first event that was emitted."""
        return self.events[0]
