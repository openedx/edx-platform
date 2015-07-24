"""Ensure videos emit proper events"""

import datetime
import json
from nose.plugins.attrib import attr
import ddt

from ..helpers import EventsTestMixin
from .test_video_module import VideoBaseTest
from ...pages.lms.video.video import _parse_time_str

from openedx.core.lib.tests.assertions.events import assert_event_matches, assert_events_equal
from opaque_keys.edx.keys import UsageKey, CourseKey


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
        self.assertIn(field, event_dict, '{0} not found in the root of the event'.format(field))
        self.assertTrue(
            isinstance(event_dict[field], field_type),
            'Expected "{key}" to be a "{field_type}", but it has the value "{value}" of type "{t}"'.format(
                key=field,
                value=event_dict[field],
                t=type(event_dict[field]),
                field_type=field_type,
            )
        )


class VideoEventsTest(VideoEventsTestMixin):
    """ Test video player event emission """

    @skip("Failing on Cypress")
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
            self.assert_field_type(load_video_event, field, basestring)
            self.assertIn(field, load_video_event, '{0} not found in the root of the event'.format(field))
            del load_video_event[field]

        # A weak assertion for the timestamp as well
        self.assert_field_type(load_video_event, 'time', datetime.datetime)
        del load_video_event['time']

        # Note that all unpredictable fields have been deleted from the event at this point

        course_key = CourseKey.from_string(self.course_id)
        static_fields_pattern = {
            'context': {
                'course_id': unicode(course_key),
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


@attr('shard_8')
@ddt.ddt
class VideoBumperEventsTest(VideoEventsTestMixin):
    """ Test bumper video event emission """

    # helper methods
    def watch_video_and_skip(self):
        """
        Wait 5 seconds and press "skip" button.
        """
        self.video.wait_for_position('0:05')
        self.video.click_player_button('skip_bumper')

    def watch_video_and_dismiss(self):
        """
        Wait 5 seconds and press "do not show again" button.
        """
        self.video.wait_for_position('0:05')
        self.video.click_player_button('do_not_show_again')

    def wait_for_state(self, state='finished'):
        """
        Wait until video will be in given state.

        Finished state means that video is played to the end.
        """
        self.video.wait_for_state(state)

    def add_bumper(self):
        """
        Add video bumper to the course.
        """
        additional_data = {
            u'video_bumper': {
                u'value': {
                    "transcripts": {},
                    "video_id": "video_001"
                }
            }
        }
        self.course_fixture.add_advanced_settings(additional_data)

    @ddt.data(
        ('edx.video.bumper.skipped', watch_video_and_skip),
        ('edx.video.bumper.dismissed', watch_video_and_dismiss),
        ('edx.video.bumper.stopped', wait_for_state)
    )
    @ddt.unpack
    def test_video_control_events(self, event_type, action):
        """
        Scenario: Video component with pre-roll emits events correctly
        Given the course has a Video component in "Youtube" mode with pre-roll enabled
        And I click on the video poster
        And the pre-roll video start playing
        And I watch (5 seconds/5 seconds/to the end of) it
        And I click (skip/do not show again) video button

        Then a "edx.video.bumper.loaded" event is emitted
        And a "edx.video.bumper.played" event is emitted
        And a "edx.video.bumper.skipped/dismissed/stopped" event is emitted
        And a "load_video" event is emitted
        And a "play_video" event is emitted
        """

        def is_video_event(event):
            """Filter out anything other than the video events of interest"""
            return event['event_type'] in (
                'edx.video.bumper.loaded',
                'edx.video.bumper.played',
                'edx.video.bumper.skipped',
                'edx.video.bumper.dismissed',
                'edx.video.bumper.stopped',
                'load_video',
                'play_video',
                'pause_video'
            ) and self.video.state != 'buffering'

        captured_events = []
        self.add_bumper()
        with self.capture_events(is_video_event, number_of_matches=5, captured_events=captured_events):
            self.navigate_to_video_no_render()
            self.video.click_on_poster()
            self.video.wait_for_video_bumper_render()
            sources, duration = self.video.sources[0], self.video.duration
            action(self)

        # Filter subsequent events that appear due to bufferisation: edx.video.bumper.played
        # As bumper does not emit pause event, we filter subsequent edx.video.bumper.played events from
        # the list, except first.
        filtered_events = []
        for video_event in captured_events:
            is_played_event = video_event['event_type'] == 'edx.video.bumper.played'
            appears_again = filtered_events and video_event['event_type'] == filtered_events[-1]['event_type']
            if is_played_event and appears_again:
                continue
            filtered_events.append(video_event)

        for idx, video_event in enumerate(filtered_events):
            if idx < 3:
                self.assert_bumper_payload_contains_ids(video_event, sources, duration)
            else:
                self.assert_payload_contains_ids(video_event)

            if idx == 0:
                assert_event_matches({'event_type': 'edx.video.bumper.loaded'}, video_event)
            elif idx == 1:
                assert_event_matches({'event_type': 'edx.video.bumper.played'}, video_event)
                self.assert_valid_control_event_at_time(video_event, 0)
            elif idx == 2:
                assert_event_matches({'event_type': event_type}, video_event)
            elif idx == 3:
                assert_event_matches({'event_type': 'load_video'}, video_event)
            elif idx == 4:
                assert_event_matches({'event_type': 'play_video'}, video_event)
                self.assert_valid_control_event_at_time(video_event, 0)

    def assert_bumper_payload_contains_ids(self, video_event, sources, duration):
        """
        Bumper video events should all contain "host_component_id", "bumper_id",
        "duration", "code" attributes in their payload.

        This function asserts that those fields are present and have correct values.
        """
        self.add_bumper()
        video_descriptors = self.course_fixture.get_nested_xblocks(category='video')
        video_desc = video_descriptors[0]
        video_locator = UsageKey.from_string(video_desc.locator)

        expected_event = {
            'event': {
                'host_component_id': video_locator.html_id(),
                'bumper_id': sources,
                'duration': _parse_time_str(duration),
                'code': 'html5'
            }
        }
        self.assert_events_match([expected_event], [video_event])

    def test_strict_event_format(self):
        """
        This test makes a very strong assertion about the fields present in events. The goal of it is to ensure that new
        fields are not added to all events mistakenly. It should be the only existing test that is updated when new top
        level fields are added to all events.
        """

        captured_events = []
        self.add_bumper()
        filter_event = lambda e: e['event_type'] == 'edx.video.bumper.loaded'
        with self.capture_events(filter_event, captured_events=captured_events):
            self.navigate_to_video_no_render()
            self.video.click_on_poster()

        load_video_event = captured_events[0]

        # Validate the event payload
        sources, duration = self.video.sources[0], self.video.duration
        self.assert_bumper_payload_contains_ids(load_video_event, sources, duration)

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
            self.assert_field_type(load_video_event, field, basestring)
            self.assertIn(field, load_video_event, '{0} not found in the root of the event'.format(field))
            del load_video_event[field]

        # A weak assertion for the timestamp as well
        self.assert_field_type(load_video_event, 'time', datetime.datetime)
        del load_video_event['time']

        # Note that all unpredictable fields have been deleted from the event at this point

        course_key = CourseKey.from_string(self.course_id)
        static_fields_pattern = {
            'context': {
                'course_id': unicode(course_key),
                'org_id': course_key.org,
                'path': '/event',
                'user_id': self.user_info['user_id']
            },
            'event_source': 'browser',
            'event_type': 'edx.video.bumper.loaded',
            'username': self.user_info['username'],
            'page': self.browser.current_url,
            'referer': self.browser.current_url,
            'name': 'edx.video.bumper.loaded',
        }
        assert_events_equal(static_fields_pattern, load_video_event)
