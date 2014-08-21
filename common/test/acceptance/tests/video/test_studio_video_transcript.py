# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Transcripts.

For transcripts acceptance tests there are 3 available caption
files. They can be used to test various transcripts features. Two of
them can be imported from YouTube.

The length of each file name is 11 characters. This is because the
YouTube's ID length is 11 characters. If file name is not of length 11,
front-end validation will not pass.

    t__eq_exist - this file exists on YouTube, and can be imported
                  via the transcripts menu; after import, this file will
                  be equal to the one stored locally
    t_neq_exist - same as above, except local file will differ from the
                  one stored on YouTube
    t_not_exist - this file does not exist on YouTube; it exists locally
"""

from .test_studio_video_module import CMSVideoBaseTest


class VideoTranscriptTest(CMSVideoBaseTest):
    """
    CMS Video Transcript Test Class
    """

    def setUp(self):
        super(VideoTranscriptTest, self).setUp()

    def _create_video_component(self, subtitles=False, subtitle_id='OEoXaMPEzfM'):
        """
        Create a video component and navigate to unit page

        Arguments:
            subtitles (bool): Upload subtitles or not
            subtitle_id (str): subtitle file id

        """
        if subtitles:
            self.assets.append('subs_{}.srt.sjson'.format(subtitle_id))

        self.navigate_to_course_unit()

    def test_input_validation(self):
        """
        Scenario: Check input error messages
        Given I have created a Video component
        Entering "123.webm" and "456.webm" source to field number 1 and 2 respectively should disable field 1 and 3
        Then I see error message "Link types should be unique."
        When I clear fields, input fields should be enabled
        And I enter a "http://link.c" source to field number 1 should disable fields 2 and 3
        Then I see error message "Incorrect url format."
        Entering "http://goo.gl/pxxZrg" source to both field number 1 and 2 should disable fields 1 and 3
        Then I see error message "Links should be unique."
        When I clear fields, input fields should be enabled
        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I do not see error message
        And I expect inputs are enabled
        """
        self._create_video_component()
        self.edit_component()
        #User inputs html5 links with equal extension
        self.video.set_url_field('123.webm', 1)
        self.video.set_url_field('456.webm', 2)
        self.assertEqual(self.video.message('error'), 'Link types should be unique.')
        # Currently we are working with 2nd field. It means, that if 2nd field
        # contain incorrect value, 1st and 3rd fields should be disabled until
        # 2nd field will be filled by correct correct value
        self.assertEqual(self.video.url_field_status(1, 3).values(), [False, False])
        self.video.clear_fields()
        self.assertEqual(self.video.url_field_status().values(), [True, True, True])
        #User input URL with incorrect format
        self.video.set_url_field('http://link.c', 1)
        self.assertEqual(self.video.message('error'), 'Incorrect url format.')
        self.assertEqual(self.video.url_field_status(2, 3).values(), [False, False])
        #User input URL with incorrect format
        self.video.set_url_field('http://goo.gl/pxxZrg', 1)
        self.video.set_url_field('http://goo.gl/pxxZrg', 2)
        self.assertEqual(self.video.message('error'), 'Links should be unique.')
        self.assertEqual(self.video.url_field_status(1, 3).values(), [False, False])
        self.video.clear_fields()
        self.assertEqual(self.video.url_field_status().values(), [True, True, True])
        self.video.set_url_field('http://youtu.be/t_not_exist', 1)
        self.assertEqual(self.video.message('error'), '')
        self.assertEqual(self.video.url_field_status().values(), [True, True, True])

    def test_youtube_server_interaction(self):
        """
        Scenario: Testing interaction with test youtube server
        Given I have created a Video component with subtitles
        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "No EdX Timed Transcript"
        And I see button "import"
        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "No Timed Transcript"
        And I do not see button "import"
        And I see button "disabled_download_to_edit"
        """
        self._create_video_component(subtitles=True)
        self.edit_component()
        # first part of url will be substituted by mock_youtube_server address
        # for t__eq_exist id server will respond with transcripts
        self.video.set_url_field('http://youtu.be/t__eq_exist', 1)
        self.assertEqual(self.video.message('status'), 'No EdX Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('import'))
        self.video.set_url_field('http://youtu.be/t_not_exist', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.assertFalse(self.video.is_transcript_button_visible('import'))
        self.assertTrue(self.video.is_transcript_button_visible('disabled_download_to_edit'))

    def test_youtube_id_w_found_state(self):
        """
        Scenario: Youtube id only: check "Found" state
        Given I have created a Video component with subtitles "t_not_exist"
        And I enter a "http://youtu.be/t_not_exist" source to field number 1
        Then I see status message "Timed Transcript Found"
        And I see value "t_not_exist" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()
        self.video.set_url_field('http://youtu.be/t_not_exist', 1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 't_not_exist'))

    def test_youtube_id_w_same_local_server_subs(self):
        """
        Scenario: Youtube id only: check "Found" state when user sets youtube_id with same local and server subs
        Given I have created a Video component with subtitles "t__eq_exist"
        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        And I see status message "Timed Transcript Found"
        And I see value "t__eq_exist" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t__eq_exist')
        self.edit_component()
        self.video.set_url_field('http://youtu.be/t__eq_exist', 1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 't__eq_exist'))

    def test_youtube_id_w_different_local_server_sub(self):
        """
        Scenario: Youtube id only: check "Found" state when user sets youtube_id with different local and server subs
        Given I have created a Video component with subtitles "t_neq_exist"
        And I enter a "http://youtu.be/t_neq_exist" source to field number 1
        And I see status message "Timed Transcript Conflict"
        And I see button "replace"
        And I click transcript button "replace"
        And I see status message "Timed Transcript Found"
        And I see value "t_neq_exist" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_neq_exist')
        self.edit_component()
        self.video.set_url_field('http://youtu.be/t_neq_exist', 1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Conflict')
        self.assertTrue(self.video.is_transcript_button_visible('replace'))
        self.video.click_button('replace')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 't_neq_exist'))

    def test_html5_source_w_not_found_state(self):
        """
        Scenario: html5 source only: check "Not Found" state
        Given I have created a Video component
        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "No Timed Transcript"
        And I see value "" in the field "Default Timed Transcript"
        """
        self._create_video_component()
        self.edit_component()
        self.video.set_url_field('t_not_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', ''))

    def test_html5_source_w_found_state(self):
        """
        Scenario: html5 source only: check "Found" state
        Given I have created a Video component with subtitles "t_not_exist"
        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "Timed Transcript Found"
        And I see value "t_not_exist" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()
        self.video.set_url_field('t_not_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 't_not_exist'))

    def test_set_youtube_id_wo_server(self):
        """
        Scenario: User sets youtube_id w/o server but with local subs and one html5 link w/o subs
        Given I have created a Video component with subtitles "t_not_exist"
        urls = ['http://youtu.be/t_not_exist', 'test_video_name.mp4']
        for each url in urls do the following
            Enter `url` to field number n
            Status message "Timed Transcript Found" is shown
        And I see value "t_not_exist" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()
        urls = ['http://youtu.be/t_not_exist', 'test_video_name.mp4']
        for index, url in enumerate(urls, 1):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'Timed Transcript Found')

        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 't_not_exist'))

    def test_set_youtube_id_wo_local(self):
        """
        Scenario: User sets youtube_id w/o local but with server subs and one html5 link w/o
                  transcripts w/o import action, then another one html5 link w/o transcripts
        Given I have created a Video component
        urls = ['http://youtu.be/t__eq_exist', 't_not_exist.mp4', 't_not_exist.webm']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `No EdX Timed Transcript` is shown
            `import` and `upload_new_timed_transcripts` are shown
        """
        self._create_video_component()
        self.edit_component()
        urls = ['http://youtu.be/t__eq_exist', 't_not_exist.mp4', 't_not_exist.webm']
        for index, url in enumerate(urls, 1):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'No EdX Timed Transcript')
            self.assertTrue(self.video.is_transcript_button_visible('import'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
