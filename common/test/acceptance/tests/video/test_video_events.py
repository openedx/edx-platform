"""Ensure videos emit proper events"""


import datetime
import json

import six
from opaque_keys.edx.keys import CourseKey, UsageKey

from common.test.acceptance.tests.helpers import EventsTestMixin
from common.test.acceptance.tests.video.test_video_module import VideoBaseTest
from openedx.core.lib.tests.assertions.events import assert_event_matches, assert_events_equal


class VideoEventsTestMixin(EventsTestMixin, VideoBaseTest):
    """
    Useful helper methods to test video player event emission.
    """
    def assert_payload_contains_ids(self, video_event):
        """
        Video events should all contain "id" and "code" attributes in their payload.

        This function asserts that those fields are present and have correct values.
        """
        video_descriptors = self.course_fixture.get_nested_xblocks(category='video')
        video_desc = video_descriptors[0]
        video_locator = UsageKey.from_string(video_desc.locator)

        expected_event = {
            'event': {
                'id': video_locator.html_id(),
                'code': '3_yD_cEKoCk'
            }
        }
        self.assert_events_match([expected_event], [video_event])

    def assert_valid_control_event_at_time(self, video_event, time_in_seconds):
        """
        Video control events should contain valid ID fields and a valid "currentTime" field.

        This function asserts that those fields are present and have correct values.
        """
        current_time = json.loads(video_event['event'])['currentTime']
        self.assertAlmostEqual(current_time, time_in_seconds, delta=1)

    def assert_field_type(self, event_dict, field, field_type):
        """Assert that a particular `field` in the `event_dict` has a particular type"""
        self.assertIn(field, event_dict, u'{0} not found in the root of the event'.format(field))
        self.assertTrue(
            isinstance(event_dict[field], field_type),
            u'Expected "{key}" to be a "{field_type}", but it has the value "{value}" of type "{t}"'.format(
                key=field,
                value=event_dict[field],
                t=type(event_dict[field]),
                field_type=field_type,
            )
        )


class VideoEventsTest(VideoEventsTestMixin):
    """ Test video player event emission """
    shard = 21

    def test_video_control_events(self):
        """
        Scenario: Video component is rendered in the LMS in Youtube mode without HTML5 sources
        Given the course has a Video component in "Youtube" mode
        And I play the video
        And I watch 5 seconds of it
        And I pause the video
        Then a "load_video" event is emitted
        And a "play_video" event is emitted
        And a "pause_video" event is emitted
        """

        def is_video_event(event):
            """Filter out anything other than the video events of interest"""
            return event['event_type'] in ('load_video', 'play_video', 'pause_video')

        captured_events = []
        with self.capture_events(is_video_event, number_of_matches=3, captured_events=captured_events):
            self.navigate_to_video()
            self.video.click_player_button('play')
            self.video.wait_for_position('0:05')
            self.video.click_player_button('pause')

        for idx, video_event in enumerate(captured_events):
            self.assert_payload_contains_ids(video_event)
            if idx == 0:
                assert_event_matches({'event_type': 'load_video'}, video_event)
            elif idx == 1:
                assert_event_matches({'event_type': 'play_video'}, video_event)
                self.assert_valid_control_event_at_time(video_event, 0)
            elif idx == 2:
                assert_event_matches({'event_type': 'pause_video'}, video_event)
                self.assert_valid_control_event_at_time(video_event, self.video.seconds)

    def test_strict_event_format(self):
        """
        This test makes a very strong assertion about the fields present in events. The goal of it is to ensure that new
        fields are not added to all events mistakenly. It should be the only existing test that is updated when new top
        level fields are added to all events.
        """

        captured_events = []
        with self.capture_events(lambda e: e['event_type'] == 'load_video', captured_events=captured_events):
            self.navigate_to_video()

        load_video_event = captured_events[0]

        # Validate the event payload
        self.assert_payload_contains_ids(load_video_event)

        # We cannot predict the value of these fields so we make weaker assertions about them
        dynamic_string_fields = (
            'accept_language',
            'agent',
            'host',
            'ip',
            'event',
            'session'
        )
        for field in dynamic_string_fields:
            self.assert_field_type(load_video_event, field, six.string_types)
            self.assertIn(field, load_video_event, u'{0} not found in the root of the event'.format(field))
            del load_video_event[field]

        # A weak assertion for the timestamp as well
        self.assert_field_type(load_video_event, 'time', datetime.datetime)
        del load_video_event['time']

        # Note that all unpredictable fields have been deleted from the event at this point

        course_key = CourseKey.from_string(self.course_id)
        static_fields_pattern = {
            'context': {
                'course_id': six.text_type(course_key),
                'org_id': course_key.org,
                'path': '/event',
                'user_id': self.user_info['user_id']
            },
            'event_source': 'browser',
            'event_type': 'load_video',
            'username': self.user_info['username'],
            'page': self.browser.current_url,
            'referer': self.browser.current_url,
            'name': 'load_video',
        }
        assert_events_equal(static_fields_pattern, load_video_event)


class VideoHLSEventsTest(VideoEventsTestMixin):
    """
    Test video player event emission for HLS video
    """
    shard = 19

    def test_event_data_for_hls(self):
        """
        Scenario: Video component with HLS video emits events correctly

        Given the course has a Video component with Youtube, HTML5 and HLS sources available.
        And I play the video
        And the video starts playing
        And I watch 3 seconds of it
        When I pause and seek the video
        And I play the video to the end
        Then I verify that all expected events are triggered
        And triggered events have correct data
        """
        video_events = ('load_video', 'play_video', 'pause_video', 'seek_video')

        def is_video_event(event):
            """
            Filter out anything other than the video events of interest
            """
            return event['event_type'] in video_events

        captured_events = []
        with self.capture_events(is_video_event, captured_events=captured_events):
            self.metadata = self.metadata_for_mode('hls')
            self.navigate_to_video()
            self.video.click_player_button('play')
            self.video.wait_for_position('0:03')
            self.video.click_player_button('pause')
            self.video.seek('0:08')

        expected_events = [{'name': event, 'event': {'code': 'hls'}} for event in video_events]
        self.assert_events_match(expected_events, captured_events)
