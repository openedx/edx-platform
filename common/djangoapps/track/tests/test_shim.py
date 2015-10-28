"""Ensure emitted events contain the fields legacy processors expect to find."""

from mock import sentinel
from django.test.utils import override_settings

from openedx.core.lib.tests.assertions.events import assert_events_equal
from track.tests import EventTrackingTestCase, FROZEN_TIME


LEGACY_SHIM_PROCESSOR = [
    {
        'ENGINE': 'track.shim.LegacyFieldMappingProcessor'
    }
]

GOOGLE_ANALYTICS_PROCESSOR = [
    {
        'ENGINE': 'track.shim.GoogleAnalyticsProcessor'
    }
]


@override_settings(
    EVENT_TRACKING_PROCESSORS=LEGACY_SHIM_PROCESSOR,
)
class LegacyFieldMappingProcessorTestCase(EventTrackingTestCase):
    """Ensure emitted events contain the fields legacy processors expect to find."""

    def test_event_field_mapping(self):
        data = {sentinel.key: sentinel.value}

        context = {
            'accept_language': sentinel.accept_language,
            'referer': sentinel.referer,
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
            'accept_language': sentinel.accept_language,
            'referer': sentinel.referer,
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
        assert_events_equal(expected_event, emitted_event)

    def test_missing_fields(self):
        self.tracker.emit(sentinel.name)

        emitted_event = self.get_event()

        expected_event = {
            'accept_language': '',
            'referer': '',
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
        assert_events_equal(expected_event, emitted_event)


@override_settings(
    EVENT_TRACKING_PROCESSORS=GOOGLE_ANALYTICS_PROCESSOR,
)
class GoogleAnalyticsProcessorTestCase(EventTrackingTestCase):
    """Ensure emitted events contain the fields necessary for Google Analytics."""

    def test_event_fields(self):
        """ Test that course_id is added as the label if present, and nonInteraction is set. """
        data = {sentinel.key: sentinel.value}

        context = {
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
            'context': context,
            'data': data,
            'label': sentinel.course_id,
            'name': sentinel.name,
            'nonInteraction': 1,
            'timestamp': FROZEN_TIME,
        }
        assert_events_equal(expected_event, emitted_event)

    def test_no_course_id(self):
        """ Test that a label is not added if course_id is not specified, but nonInteraction is still set. """
        data = {sentinel.key: sentinel.value}

        context = {
            'path': sentinel.path,
            'user_id': sentinel.user_id,
            'client_id': sentinel.client_id,
        }
        with self.tracker.context('test', context):
            self.tracker.emit(sentinel.name, data)

        emitted_event = self.get_event()

        expected_event = {
            'context': context,
            'data': data,
            'name': sentinel.name,
            'nonInteraction': 1,
            'timestamp': FROZEN_TIME,
        }
        assert_events_equal(expected_event, emitted_event)
