"""
Acceptance tests for Video Times(Start, End and Finish) functionality.
"""

from .test_video_module import VideoBaseTest
from unittest import skip


class VideoTimesTest(VideoBaseTest):
    """ Test Video Player Times """

    def setUp(self):
        super(VideoTimesTest, self).setUp()

    def test_video_start_time(self):
        """
        Scenario: Start time works for Youtube video
        Given we have a video in "Youtube" mode with start_time set to 00:00:10
        And I see video slider at "0:10" position
        And I click video button "play"
        Then video starts playing at or after start_time(00:00:10)

        """
        data = {'start_time': '00:00:10'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.assertEqual(self.video.position, '0:10')

        self.video.click_player_button('play')

        self.assertGreaterEqual(int(self.video.position.split(':')[1]), 10)

    def test_video_end_time_with_default_start_time(self):
        """
        Scenario: End time works for Youtube video if starts playing from beginning.
        Given we have a video in "Youtube" mode with end time set to 00:00:02
        And I click video button "play"
        And I wait until video stop playing
        Then I see video slider at "0:02" position

        """
        data = {'end_time': '00:00:02'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.video.click_player_button('play')

        # wait until video stop playing
        self.video.wait_for_state('pause')

        self.assertEqual(self.video.position, '0:02')

    def test_video_end_time_wo_default_start_time(self):
        """
        Scenario: End time works for Youtube video if starts playing from between.
        Given we have a video in "Youtube" mode  with end time set to 00:01:00
        And I seek video to "0:55" position
        And I click video button "play"
        And I wait until video stop playing
        Then I see video slider at "1:00" position

        """
        data = {'end_time': '00:01:00'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.video.seek('0:55')

        self.video.click_player_button('play')

        # wait until video stop playing
        self.video.wait_for_state('pause')

        self.assertEqual(self.video.position, '1:00')

    def test_video_start_time_and_end_time(self):
        """
        Scenario: Start time and end time work together for Youtube video.
        Given we a video in "Youtube" mode with start time set to 00:00:10 and end_time set to 00:00:12
        And I see video slider at "0:10" position
        And I click video button "play"
        Then I wait until video stop playing
        Then I see video slider at "0:12" position

        """
        data = {'start_time': '00:00:10', 'end_time': '00:00:12'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.assertEqual(self.video.position, '0:10')

        self.video.click_player_button('play')

        # wait until video stop playing
        self.video.wait_for_state('pause')

        self.assertEqual(self.video.position, '0:12')

    @skip("Intermittently fails 03 June 2014")
    def test_video_end_time_and_finish_time(self):
        """
        Scenario: Youtube video works after pausing at end time and then plays again from End Time to the end.
        Given we have a video in "Youtube" mode with start time set to 00:01:41 and end_time set to 00:01:42
        And I click video button "play"
        And I wait until video stop playing
        Then I see video slider at "1:42" position
        And I click video button "play"
        And I wait until video stop playing
        Then I see video slider at "1:54" position
        # NOTE: The above video duration(1:54) is disputed because
        # 1. Our Video Player first shows Video Duration equals to 1 minute and 56 sec and then 1 minute and 54 sec
        # 2  YouTube first shows duration of 1 minute and 56 seconds and then changes duration to 1 minute and 55 sec
        #
        # The 1:56 time is the duration from metadata. 1:54 time is the duration reported by the video API once
        # the video starts playing. BUT sometime video API gives duration equals 1 minute and 55 second.

        """
        data = {'start_time': '00:01:41', 'end_time': '00:01:42'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.video.click_player_button('play')

        # wait until video stop playing
        self.video.wait_for_state('pause')

        self.assertEqual(self.video.position, '1:42')

        self.video.click_player_button('play')

        # wait until video stop playing
        self.video.wait_for_state('finished')

        self.assertIn(self.video.position, ['1:54', '1:55'])

    def test_video_end_time_with_seek(self):
        """
        Scenario: End Time works for Youtube Video if starts playing before Start Time.
        Given we have a video in "Youtube" mode with end-time at 0:32 and start-time at 0:30
        And I seek video to "0:28" position
        And I click video button "play"
        And I wait until video stop playing
        Then I see video slider at "0:32" position

        """
        data = {'start_time': '00:00:30', 'end_time': '00:00:32'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.video.seek('0:28')

        self.video.click_player_button('play')

        # wait until video stop playing
        self.video.wait_for_state('pause')

        self.assertEqual(self.video.position, '0:32')

    def test_video_finish_time_with_seek(self):
        """
        Scenario: Finish Time works for Youtube video.
        Given it has a video in "Youtube" mode with end-time at 1:00, the video starts playing from 1:42
        And I seek video to "1:42" position
        And I click video button "play"
        And I wait until video stop playing
        Then I see video slider at "1:54" position
        # NOTE: The above video duration(1:54) is disputed because
        # 1. Our Video Player first shows Video Duration equals to 1 minute and 56 sec and then 1 minute and 54 sec
        # 2  YouTube first shows duration of 1 minute and 56 seconds and then changes duration to 1 minute and 55 sec
        #
        # The 1:56 time is the duration from metadata. 1:54 time is the duration reported by the video API once
        # the video starts playing. BUT sometime video API gives duration equals 1 minute and 55 second.

        """
        data = {'end_time': '00:01:00'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.video.seek('1:42')

        self.video.click_player_button('play')

        # wait until video stop playing
        self.video.wait_for_state('finished')

        self.assertIn(self.video.position, ['1:54', '1:55'])
