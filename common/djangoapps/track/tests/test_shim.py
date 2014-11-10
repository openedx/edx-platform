"""Ensure emitted events contain the fields legacy processors expect to find."""

from mock import sentinel
from django.test.utils import override_settings

from track.tests import EventTrackingTestCase, FROZEN_TIME


LEGACY_SHIM_PROCESSOR = [
    {
        'ENGINE': 'track.shim.LegacyFieldMappingProcessor'
    }
]


class LegacyFieldMappingProcessorTestCase(EventTrackingTestCase):
    """Ensure emitted events contain the fields legacy processors expect to find."""

    @override_settings(
        EVENT_TRACKING_PROCESSORS=LEGACY_SHIM_PROCESSOR,
    )
    def test_event_field_mapping(self):
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
            'client_id': sentinel.client_id,
        }
        with self.tracker.context('test', context):
            self.tracker.emit(sentinel.name, data)

        emitted_event = self.get_event()

        expected_event = {
            'event_type': sentinel.name,
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
        EVENT_TRACKING_PROCESSORS=LEGACY_SHIM_PROCESSOR,
    )
    def test_missing_fields(self):
        self.tracker.emit(sentinel.name)

        emitted_event = self.get_event()

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
