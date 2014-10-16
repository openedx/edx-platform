"""Ensure we can parse events sent to us from the segment.io webhook integration"""

from datetime import datetime
import json

from ddt import ddt, data
from freezegun import freeze_time
from mock import patch, sentinel

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from track.middleware import TrackMiddleware
from track.views import segmentio


EXPECTED_TIME = datetime(2013, 10, 3, 8, 24, 55)
SECRET = 'anything'
ENDPOINT = '/segmentio/test/event'
USER_ID = 10


@ddt
@override_settings(
    TRACKING_SEGMENTIO_WEBHOOK_SECRET=SECRET,
    TRACKING_IGNORE_URL_PATTERNS=[ENDPOINT],
    TRACKING_SEGMENTIO_ALLOWED_ACTIONS=['Track', 'Screen'],
    TRACKING_SEGMENTIO_ALLOWED_CHANNELS=['mobile']
)
@freeze_time(EXPECTED_TIME)
class SegmentIOTrackingTestCase(TestCase):
    """Test processing of segment.io events"""

    def setUp(self):
        self.request_factory = RequestFactory()

        patcher = patch('track.views.segmentio.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def test_segmentio_tracking_get_request(self):
        request = self.request_factory.get(ENDPOINT)
        response = segmentio.track_segmentio_event(request)
        self.assertEquals(response.status_code, 405)
        self.assertFalse(self.mock_tracker.send.called)  # pylint: disable=maybe-no-member

    @override_settings(
        TRACKING_SEGMENTIO_WEBHOOK_SECRET=None
    )
    def test_segmentio_tracking_no_secret_config(self):
        request = self.request_factory.post(ENDPOINT)
        response = segmentio.track_segmentio_event(request)
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_UNAUTHORIZED, 401)

    def assert_segmentio_uncommitted_response(self, response, expected_message, expected_status=400):
        """Assert that no event was emitted and an appropriate commit==false message was returned"""
        self.assertEquals(response.status_code, expected_status)
        parsed_content = json.loads(response.content)
        self.assertEquals(parsed_content, {'committed': False, 'message': expected_message})
        self.assertFalse(self.mock_tracker.send.called)  # pylint: disable=maybe-no-member

    def test_segmentio_tracking_no_secret_provided(self):
        request = self.request_factory.post(ENDPOINT)
        response = segmentio.track_segmentio_event(request)
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_UNAUTHORIZED, 401)

    def test_segmentio_tracking_secret_mismatch(self):
        request = self.create_request(key='y')
        response = segmentio.track_segmentio_event(request)
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_UNAUTHORIZED, 401)

    def create_request(self, key=None, **kwargs):
        """Create a fake request that emulates a request from the segment.io servers to ours"""
        if key is None:
            key = SECRET

        return self.request_factory.post(ENDPOINT + "?key=" + key, **kwargs)

    @data('Identify', 'Group', 'Alias', 'Page', 'identify')
    def test_segmentio_ignore_actions(self, action):
        response = self.post_segmentio_event(action=action)
        self.assert_segmentio_uncommitted_response(response, segmentio.WARNING_IGNORED_ACTION, 200)

    def post_segmentio_event(self, **kwargs):
        """Post a fake segment.io event to the view that processes it"""
        request = self.create_request(
            data=self.create_segmentio_event_json(**kwargs),
            content_type='application/json'
        )
        return segmentio.track_segmentio_event(request)

    @data('server', 'browser', 'Browser')
    def test_segmentio_ignore_channels(self, channel):
        response = self.post_segmentio_event(channel=channel)
        self.assert_segmentio_uncommitted_response(response, segmentio.WARNING_IGNORED_CHANNEL, 200)

    def create_segmentio_event(self, **kwargs):
        """Populate a fake segment.io event with data of interest"""
        action = kwargs.get('action', 'Track')
        sample_event = {
            "userId": kwargs.get('user_id', USER_ID),
            "event": "Did something",
            "properties": {
                'event_type': kwargs.get('event_type', ''),
                'event': kwargs.get('event', {}),
                'context': {
                    'course_id': kwargs.get('course_id') or '',
                }
            },
            "channel": kwargs.get('channel', 'mobile'),
            "context": {
                "library": {
                    "name": "unknown",
                    "version": "unknown"
                }
            },
            "receivedAt": "2014-08-27T16:33:39.100Z",
            "timestamp": "2014-08-27T16:33:39.215Z",
            "type": action.lower(),
            "projectId": "u0j33yjkr8",
            "messageId": "qy52hwp4",
            "version": 2,
            "integrations": {},
            "options": {
                "library": "unknown",
                "providers": {}
            },
            "action": action
        }
        return sample_event

    def create_segmentio_event_json(self, **kwargs):
        """Return a json string containing a fake segment.io event"""
        return json.dumps(self.create_segmentio_event(**kwargs))

    def test_segmentio_tracking_no_user_for_user_id(self):
        response = self.post_segmentio_event(user_id=40)
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_USER_NOT_EXIST, 400)

    def test_segmentio_tracking_invalid_user_id(self):
        response = self.post_segmentio_event(user_id='foobar')
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_INVALID_USER_ID, 400)

    @data('foo/bar/baz', 'course-v1:foo+bar+baz')
    def test_segmentio_tracking(self, course_id):
        middleware = TrackMiddleware()

        request = self.create_request(
            data=self.create_segmentio_event_json(event_type=str(sentinel.event_type), event={'foo': 'bar'}, course_id=course_id),
            content_type='application/json'
        )
        User.objects.create(pk=USER_ID, username=str(sentinel.username))

        middleware.process_request(request)
        # The middleware normally emits an event, make sure it doesn't in this case.
        self.assertFalse(self.mock_tracker.send.called)  # pylint: disable=maybe-no-member
        try:
            response = segmentio.track_segmentio_event(request)
            self.assertEquals(response.status_code, 200)

            expected_event = {
                'username': str(sentinel.username),
                'ip': '',
                'event_source': 'mobile',
                'event_type': str(sentinel.event_type),
                'event': {'foo': 'bar'},
                'agent': '',
                'page': None,
                'time': datetime.strptime("2014-08-27T16:33:39.215Z", "%Y-%m-%dT%H:%M:%S.%fZ"),
                'host': 'testserver',
                'context': {
                    'user_id': USER_ID,
                    'course_id': course_id,
                    'org_id': 'foo',
                    'path': ENDPOINT,
                    'client': {
                        'library': {
                            'name': 'unknown',
                            'version': 'unknown'
                        }
                    },
                    'received_at': datetime.strptime("2014-08-27T16:33:39.100Z", "%Y-%m-%dT%H:%M:%S.%fZ"),
                },
            }
        finally:
            middleware.process_response(request, None)

        self.mock_tracker.send.assert_called_once_with(expected_event)  # pylint: disable=maybe-no-member

    def test_segmentio_tracking_invalid_course_id(self):
        request = self.create_request(
            data=self.create_segmentio_event_json(course_id='invalid'),
            content_type='application/json'
        )
        User.objects.create(pk=USER_ID, username=str(sentinel.username))
        response = segmentio.track_segmentio_event(request)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.mock_tracker.send.called)  # pylint: disable=maybe-no-member

    def test_segmentio_tracking_missing_event_type(self):
        sample_event_raw = self.create_segmentio_event()
        sample_event_raw['properties'] = {}
        request = self.create_request(
            data=json.dumps(sample_event_raw),
            content_type='application/json'
        )
        User.objects.create(pk=USER_ID, username=str(sentinel.username))

        response = segmentio.track_segmentio_event(request)
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_MISSING_EVENT_TYPE, 400)

    def test_segmentio_tracking_missing_timestamp(self):
        sample_event_raw = self.create_event_without_fields('timestamp')
        request = self.create_request(
            data=json.dumps(sample_event_raw),
            content_type='application/json'
        )
        User.objects.create(pk=USER_ID, username=str(sentinel.username))

        response = segmentio.track_segmentio_event(request)
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_MISSING_TIMESTAMP, 400)

    def create_event_without_fields(self, *fields):
        """Create a fake event and remove some fields from it"""
        event = self.create_segmentio_event()

        for field in fields:
            if field in event:
                del event[field]

        return event

    def test_segmentio_tracking_missing_received_at(self):
        sample_event_raw = self.create_event_without_fields('receivedAt')
        request = self.create_request(
            data=json.dumps(sample_event_raw),
            content_type='application/json'
        )
        User.objects.create(pk=USER_ID, username=str(sentinel.username))

        response = segmentio.track_segmentio_event(request)
        self.assert_segmentio_uncommitted_response(response, segmentio.ERROR_MISSING_RECEIVED_AT, 400)
