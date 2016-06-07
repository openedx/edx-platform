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
from nose.plugins.attrib import attr
from .test_studio_video_module import CMSVideoBaseTest


@attr('shard_6')
class VideoTranscriptTest(CMSVideoBaseTest):
    """
    CMS Video Transcript Test Class
    """

    def setUp(self):
        super(VideoTranscriptTest, self).setUp()

    def _create_video_component(self, subtitles=False, subtitle_id='3_yD_cEKoCk'):
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
        self.video.click_button_subtitles()
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

    def test_youtube_no_import(self):
        """
        Scenario: Entering youtube (no importing), and 2 html5 sources without transcripts - "Not Found"
        Given I have created a Video component

        urls = ['http://youtu.be/t_not_exist', 't_not_exist.mp4', 't_not_exist.webm']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `No Timed Transcript` is shown
            `disabled_download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        """
        self._create_video_component()
        self.edit_component()

        urls = ['http://youtu.be/t_not_exist', 't_not_exist.mp4', 't_not_exist.webm']
        for index, url in enumerate(urls, 1):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'No Timed Transcript')
            self.assertTrue(self.video.is_transcript_button_visible('disabled_download_to_edit'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

    def test_youtube_with_import(self):
        """
        Scenario: Entering youtube with imported transcripts, and 2 html5 sources without transcripts - "Found"
        Given I have created a Video component

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "No EdX Timed Transcript"
        And I see button "import"
        And I click transcript button "import"
        Then I see status message "Timed Transcript Found"
        And I see button "upload_new_timed_transcripts"

        urls = ['t_not_exist.mp4', 't_not_exist.webm']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `Timed Transcript Found` is shown
            `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('http://youtu.be/t__eq_exist', 1)
        self.assertEqual(self.video.message('status'), 'No EdX Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('import'))
        self.video.click_button('import')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

        urls = ['t_not_exist.mp4', 't_not_exist.webm']
        for index, url in enumerate(urls, 2):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
            self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

    def test_youtube_wo_transcripts(self):
        """
        Scenario: Entering youtube w/o transcripts - html5 w/o transcripts - html5 with transcripts
        Given I have created a Video component with subtitles "t_neq_exist"

        urls = ['http://youtu.be/t_not_exist', 't_not_exist.mp4']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `No Timed Transcript` is shown
            `disabled_download_to_edit` and `upload_new_timed_transcripts` buttons are shown

        And I enter a "t_neq_exist.webm" source to field number 3
        Then I see status message "Timed Transcript Found"
        `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        """
        self._create_video_component(subtitles=True, subtitle_id='t_neq_exist')
        self.edit_component()

        urls = ['http://youtu.be/t_not_exist', 't_not_exist.mp4']
        for index, url in enumerate(urls, 1):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'No Timed Transcript')
            self.assertTrue(self.video.is_transcript_button_visible('disabled_download_to_edit'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

        self.video.set_url_field('t_neq_exist.webm', 3)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

    def test_youtube_wo_imported_transcripts(self):
        """
        Scenario: Entering youtube w/o imported transcripts - html5 w/o transcripts w/o import - html5 with transcripts
        Given I have created a Video component with subtitles "t_neq_exist"

        urls = ['http://youtu.be/t__eq_exist', 't_not_exist.mp4', 't_neq_exist.webm']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `No EdX Timed Transcript` is shown
            `import` and `upload_new_timed_transcripts` buttons are shown
        """
        self._create_video_component(subtitles=True, subtitle_id='t_neq_exist')
        self.edit_component()

        urls = ['http://youtu.be/t__eq_exist', 't_not_exist.mp4', 't_neq_exist.webm']
        for index, url in enumerate(urls, 1):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'No EdX Timed Transcript')
            self.assertTrue(self.video.is_transcript_button_visible('import'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

    def test_youtube_wo_imported_transcripts2(self):
        """
        Scenario: Entering youtube w/o imported transcripts - html5 with transcripts - html5 w/o transcripts w/o import
        Given I have created a Video component with subtitles "t_neq_exist"

        urls = ['http://youtu.be/t__eq_exist', 't_neq_exist.mp4', 't_not_exist.webm']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `No EdX Timed Transcript` is shown
            `import` and `upload_new_timed_transcripts` buttons are shown
        """
        self._create_video_component(subtitles=True, subtitle_id='t_neq_exist')
        self.edit_component()

        urls = ['http://youtu.be/t__eq_exist', 't_neq_exist.mp4', 't_not_exist.webm']
        for index, url in enumerate(urls, 1):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'No EdX Timed Transcript')
            self.assertTrue(self.video.is_transcript_button_visible('import'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

    def test_youtube_w_imported_transcripts(self):
        """
        Scenario: Entering youtube with imported transcripts - html5 with transcripts - html5 w/o transcripts
        Given I have created a Video component with subtitles "t_neq_exist"

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "No EdX Timed Transcript"
        And I see button "import"
        And I click transcript button "import"
        Then I see status message "Timed Transcript Found"
        And I see button "upload_new_timed_transcripts"

        urls = ['t_neq_exist.mp4', 't_not_exist.webm']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `Timed Transcript Found` is shown
            `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        """
        self._create_video_component(subtitles=True, subtitle_id='t_neq_exist')
        self.edit_component()

        self.video.set_url_field('http://youtu.be/t__eq_exist', 1)
        self.assertEqual(self.video.message('status'), 'No EdX Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('import'))
        self.video.click_button('import')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

        urls = ['t_neq_exist.mp4', 't_not_exist.webm']
        for index, url in enumerate(urls, 2):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
            self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

    def test_youtube_w_imported_transcripts2(self):
        """
        Scenario: Entering youtube with imported transcripts - html5 w/o transcripts - html5 with transcripts
        Given I have created a Video component with subtitles "t_neq_exist"

        And I enter a "http://youtu.be/t__eq_exist" source to field number 1
        Then I see status message "No EdX Timed Transcript"
        And I see button "import"
        And I click transcript button "import"
        Then I see status message "Timed Transcript Found"
        And I see button "upload_new_timed_transcripts"

        urls = ['t_not_exist.mp4', 't_neq_exist.webm']
        for each url in urls do the following
            Enter `url` to field number `n`
            Status message `Timed Transcript Found` is shown
            `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        """
        self._create_video_component(subtitles=True, subtitle_id='t_neq_exist')
        self.edit_component()

        self.video.set_url_field('http://youtu.be/t__eq_exist', 1)
        self.assertEqual(self.video.message('status'), 'No EdX Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('import'))
        self.video.click_button('import')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

        urls = ['t_not_exist.mp4', 't_neq_exist.webm']
        for index, url in enumerate(urls, 2):
            self.video.set_url_field(url, index)
            self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
            self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
            self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

    def test_html5_with_transcripts(self):
        """
        Scenario: Entering html5 with transcripts - upload - youtube w/o transcripts
        Given I have created a Video component with subtitles "t__eq_exist"

        And I enter a "t__eq_exist.mp4" source to field number 1
        Then I see status message "Timed Transcript Found"
        `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "Timed Transcript Uploaded Successfully"
        `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        And I see value "t__eq_exist" in the field "Default Timed Transcript"

        And I enter a "http://youtu.be/t_not_exist" source to field number 2
        Then I see status message "Timed Transcript Found"
        `download_to_edit` and `upload_new_timed_transcripts` buttons are shown

        And I enter a "uk_transcripts.webm" source to field number 3
        Then I see status message "Timed Transcript Found"
        """
        self._create_video_component(subtitles=True, subtitle_id='t__eq_exist')
        self.edit_component()

        self.video.set_url_field('t__eq_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 't__eq_exist'))
        self.open_basic_tab()

        self.video.set_url_field('http://youtu.be/t_not_exist', 2)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

        self.video.set_url_field('uk_transcripts.webm', 3)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')

    def test_two_html5_sources_w_transcripts(self):
        """
        Scenario: Enter 2 HTML5 sources with transcripts, they are not the same, choose
        Given I have created a Video component with subtitles "t_not_exist"

        And I enter a "uk_transcripts.mp4" source to field number 1
        Then I see status message "No Timed Transcript"
        `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "Timed Transcript Uploaded Successfully"
        And I see value "uk_transcripts" in the field "Default Timed Transcript"

        And I enter a "t_not_exist.webm" source to field number 2
        Then I see status message "Timed Transcript Conflict"
        `Timed Transcript from uk_transcripts.mp4` and `Timed Transcript from t_not_exist.webm` buttons are shown
        And I click transcript button "Timed Transcript from t_not_exist.webm"
        And I see value "uk_transcripts|t_not_exist" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()

        self.video.set_url_field('uk_transcripts.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'uk_transcripts'))
        self.open_basic_tab()

        self.video.set_url_field('t_not_exist.webm', 2)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Conflict')
        self.assertTrue(
            self.video.is_transcript_button_visible('choose', button_text='Timed Transcript from uk_transcripts.mp4'))
        self.assertTrue(self.video.is_transcript_button_visible('choose', index=1,
                                                                button_text='Timed Transcript from t_not_exist.webm'))

    def test_one_field_only(self):
        """
        Scenario: Work with 1 field only: Enter HTML5 source with transcripts - save -> change it to another one
                  HTML5 source w/o transcripts - click on use existing ->  change it to another one HTML5 source
                  w/o transcripts - do not click on use existing -> change it to another one HTML5 source w/o
                  transcripts - click on use existing
        Given I have created a Video component with subtitles "t_not_exist"

        If i enter "t_not_exist.mp4" source to field number 1 Then I see status message "Timed Transcript Found"
        `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        And I see value "t_not_exist" in the field "Default Timed Transcript"
        And I save changes And then edit the component

        If i enter "video_name_2.mp4" source to field number 1 Then I see status message "Confirm Timed Transcript"
        I see button "use_existing" And I click on it
        And I see value "video_name_2" in the field "Default Timed Transcript"

        If i enter "video_name_3.mp4" source to field number 1 Then I see status message "Confirm Timed Transcript"
        And I see button "use_existing"

        If i enter a "video_name_4.mp4" source to field number 1 Then I see status message "Confirm Timed Transcript"
        I see button "use_existing" And I click on it
        And I see value "video_name_4" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()

        self.video.set_url_field('t_not_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 't_not_exist'))
        self.open_basic_tab()
        self.save_unit_settings()
        self.edit_component()

        self.video.set_url_field('video_name_2.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Confirm Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('use_existing'))
        self.video.click_button('use_existing')
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_2'))
        self.open_basic_tab()

        self.video.set_url_field('video_name_3.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Confirm Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('use_existing'))

        self.video.set_url_field('video_name_4.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Confirm Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('use_existing'))
        self.video.click_button('use_existing')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_4'))

    def test_two_fields_only(self):
        """
        Scenario: Work with 2 fields: Enter HTML5 source with transcripts - save -> change it to another one HTML5
                  source w/o transcripts - do not click on use existing ->  add another one HTML5 source w/o
                  transcripts - click on use existing
        Given I have created a Video component with subtitles "t_not_exist"

        And I enter a "t_not_exist.mp4" source to field number 1
        Then I see status message "Timed Transcript Found"
       `download_to_edit` and `upload_new_timed_transcripts` buttons are shown
        And I save changes
        And I edit the component

        And I enter a "video_name_2.mp4" source to field number 1
        Then I see status message "Confirm Timed Transcript"
        And I see button "use_existing"

        And I enter a "video_name_3.webm" source to field number 2
        Then I see status message "Confirm Timed Transcript"
        And I see button "use_existing"
        And I click transcript button "use_existing"
        And I see value "video_name_3" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()

        self.video.set_url_field('t_not_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.is_transcript_button_visible('download_to_edit'))
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.save_unit_settings()
        self.edit_component()

        self.video.set_url_field('video_name_2.mp4', 1)
        self.assertEqual(self.video.message('status'), 'Confirm Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('use_existing'))

        self.video.set_url_field('video_name_3.webm', 2)
        self.assertEqual(self.video.message('status'), 'Confirm Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('use_existing'))
        self.video.click_button('use_existing')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_3'))

    def test_upload_subtitles(self):
        """
        Scenario: File name and name of subs are different (Uploading subtitles with different file name than file)
        Given I have created a Video component

        And I enter a "video_name_1.mp4" source to field number 1
        And I see status message "No Timed Transcript"
        And I upload the transcripts file "uk_transcripts.srt"
        Then I see status message "Timed Transcript Uploaded Successfully"
        And I see value "video_name_1" in the field "Default Timed Transcript"
        And I save changes
        Then when I view the video it does show the captions
        And I edit the component
        Then I see status message "Timed Transcript Found"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('video_name_1.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_1'))
        self.save_unit_settings()
        self.video.is_captions_visible()
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')

    def test_video_wo_subtitles(self):
        """
        Scenario: Video w/o subs - another video w/o subs - Not found message
                  Video can have filled item.sub, but doesn't have subs file.
                  In this case, after changing this video by another one without subs
                  `No Timed Transcript` message should appear ( not 'Confirm Timed Transcript').
        Given I have created a Video component

        And I enter a "video_name_1.mp4" source to field number 1
        Then I see status message "No Timed Transcript"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('video_name_1.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')

    def test_subtitles_copy(self):
        """
        Scenario: Subtitles are copied for every html5 video source
        Given I have created a Video component

        After I enter a "video_name_1.mp4" source to field number 1 Then I see status message "No Timed Transcript"

        After I enter a "video_name_2.webm" source to field number 2 Then I see status message "No Timed Transcript"
        After uploading transcript "uk_transcripts.srt" I should see message "Timed Transcript Uploaded Successfully"
        And I see value "video_name_2" in the field "Default Timed Transcript"
        When I clear field number 1 Then I see status message "Timed Transcript Found"
        And I see value "video_name_2" in the field "Default Timed Transcript"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('video_name_1.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')

        self.video.set_url_field('video_name_2.webm', 2)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_2'))
        self.open_basic_tab()
        self.video.clear_field(1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_2'))

    def test_upload_button_w_youtube(self):
        """
        Scenario: Upload button for single youtube id
        Given I have created a Video component

        After I enter a "http://youtu.be/t_not_exist" source to field number 1 I see message "No Timed Transcript"
        And I see button "upload_new_timed_transcripts"
        After I upload the transcripts file "uk_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        After saving the changes video captions should be visible
        When I edit the component Then I see status message "Timed Transcript Found"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('http://youtu.be/t_not_exist', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')

    def test_upload_button_w_html5_ids(self):
        """
        Scenario: Upload button for youtube id with html5 ids
        Given I have created a Video component

        After I enter a "http://youtu.be/t_not_exist" source to field number 1 I see message "No Timed Transcript"
        And I see button "upload_new_timed_transcripts"

        After I enter a "video_name_1.mp4" source to field number 2 Then I see status message "No Timed Transcript"
        And I see button "upload_new_timed_transcripts"
        After I upload the transcripts file "uk_transcripts.srt"I see message "Timed Transcript Uploaded Successfully"
        When I clear field number 1 Then I see status message "Timed Transcript Found"
        And I see value "video_name_1" in the field "Default Timed Transcript"
        After saving the changes video captions should be visible
        When I edit the component Then I see status message "Timed Transcript Found"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('http://youtu.be/t_not_exist', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))

        self.video.set_url_field('video_name_1.mp4', 2)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.assertTrue(self.video.is_transcript_button_visible('upload_new_timed_transcripts'))
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.video.clear_field(1)
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_1'))
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')

    def test_advanced_tab_transcript_fields(self):
        """
        Scenario: Change transcripts field in Advanced tab
        Given I have created a Video component with subtitles "t_not_exist"

        After I enter a "video_name_1.mp4" source to field number 1  Then I see status message "No Timed Transcript"
        Open tab "Advanced" and set value "t_not_exist" to the field "Default Timed Transcript"
        After saving the changes video captions should be visible
        When I edit the component Then I see status message "Timed Transcript Found"
        And I see value "video_name_1" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()

        self.video.set_url_field('video_name_1.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.open_advanced_tab()
        self.video.set_field_value('Default Timed Transcript', 't_not_exist')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_1'))

    def test_non_ascii_transcripts(self):
        """
        Scenario: Check non-ascii (chinese) transcripts
        Given I have created a Video component

        After I enter a "video_name_1.mp4" source to field number 1 Then I see status message "No Timed Transcript"
        After I upload the transcripts "chinese_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        After saving the changes video captions should be visible
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('video_name_1.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('chinese_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())

    def test_module_metadata_save(self):
        """
        Scenario: Check saving module metadata on switching between tabs
        Given I have created a Video component with subtitles "t_not_exist"

        After I enter a "video_name_1.mp4" source to field number 1 I should see status message "No Timed Transcript"
        Open tab "Advanced" and set value "t_not_exist" to the field "Default Timed Transcript"
        When I open tab "Basic" Then I see status message "Timed Transcript Found"
        After saving the changes video captions should be visible
        When I edit the component I should see status message "Timed Transcript Found"
        And I see value "video_name_1" in the field "Default Timed Transcript"
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()

        self.video.set_url_field('video_name_1.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.open_advanced_tab()
        self.video.set_field_value('Default Timed Transcript', 't_not_exist')
        self.open_basic_tab()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_1'))

    def test_clearing_transcripts_wo_save(self):
        """
        Scenario: After clearing Transcripts field in the Advanced tab "not found" message should be visible w/o saving
        Given I have created a Video component

        After I enter a "t_not_exist.mp4" source to field number 1 I should see status message "No Timed Transcript"
        After uploading transcripts "chinese_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        Open tab "Advanced" and set value "" to the field "Default Timed Transcript"
        When I open tab "Basic" I see status message "No Timed Transcript"
        After saving the changes video captions should not be visible
        When I edit the component I should see status message "No Timed Transcript"
        And I see value "" in the field "Default Timed Transcript"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('t_not_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('chinese_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.open_advanced_tab()
        self.video.set_field_value('Default Timed Transcript', '')
        self.open_basic_tab()
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', ''))

    def test_clearing_transcripts_w_save(self):
        """
        Scenario: After clearing Transcripts field in the Advanced tab "not found" message should be visible with saving
        Given I have created a Video component

        After I enter a "t_not_exist.mp4" source to field number 1 I see status message "No Timed Transcript"
        After uploading the transcripts "chinese_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        After saving changes I see "好 各位同学" text in the captions
        And I edit the component
        Open tab "Advanced" I set value "" to the field "Default Timed Transcript"
        When I open tab "Basic" I see status message "No Timed Transcript"
        After saving the changes video captions should not be visible
        After I edit the component I should see status message "No Timed Transcript"
        And I see value "" in the field "Default Timed Transcript"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('t_not_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('chinese_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.save_unit_settings()
        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.edit_component()
        self.open_advanced_tab()
        self.video.set_field_value('Default Timed Transcript', '')
        self.open_basic_tab()
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', ''))

    def test_video_w_existing_subtitles(self):
        """
        Scenario: Video with existing subs - Advanced tab - change to another one subs -
                  Basic tab - Found message - Save - see correct subs
        Given I have created a Video component with subtitles "t_not_exist"

        After I enter a "video_name_1.mp4" source to field number 1 I see status message "No Timed Transcript"
        After uploading the transcripts "chinese_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        After saving the changes video captions should be visible
        And I see "好 各位同学" text in the captions
        And I edit the component
        Open tab "Advanced" And set value "t_not_exist" to the field "Default Timed Transcript"
        When I open tab "Basic" I should see status message "Timed Transcript Found"
        After saving the changes video captions should be visible
        And I see "LILA FISHER: Hi, welcome to Edx." text in the captions
        """
        self._create_video_component(subtitles=True, subtitle_id='t_not_exist')
        self.edit_component()

        self.video.set_url_field('video_name_1.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('chinese_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.edit_component()
        self.open_advanced_tab()
        self.video.set_field_value('Default Timed Transcript', 't_not_exist')
        self.open_basic_tab()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.assertIn('LILA FISHER: Hi, welcome to Edx.', self.video.captions_text)

    def test_reverting_transcripts(self):
        """
        Scenario: After reverting Transcripts field in the Advanced tab "not found" message should be visible
        Given I have created a Video component

        After I enter a "t_not_exist.mp4" source to field number 1 Then I see status message "No Timed Transcript"
        After uploading transcripts "chinese_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        After saving the changes I should see "好 各位同学" text in the captions
        After I edit the component I open tab "Advanced"
        And I revert the transcript field "Default Timed Transcript"
        After saving the changes video captions should not be visible
        After I edit the component I should see status message "No Timed Transcript"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('t_not_exist.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('chinese_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.save_unit_settings()
        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text)
        self.edit_component()
        self.open_advanced_tab()
        self.video.revert_field('Default Timed Transcript')
        self.save_unit_settings()
        self.assertFalse(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')

    def test_upload_subtitles_w_different_names2(self):
        """
        Scenario: File name and name of subs are different -- Uploading subtitles for file with periods
                  in it should properly set the transcript name and keep the periods
        Given I have created a Video component

        After I enter a "video_name_1.1.2.mp4" source to field number 1, I see status message "No Timed Transcript"
        After I upload the transcripts file "uk_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        And I see value "video_name_1.1.2" in the field "Default Timed Transcript"
        After saving the changes video captions should be visible
        After I edit the component I should see status message "Timed Transcript Found"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('video_name_1.1.2.mp4', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'video_name_1.1.2'))
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')

    def test_upload_subtitles_w_different_names3(self):
        """
        Scenario: Shortened link: File name and name of subs are different
        Given I have created a Video component

        After I enter a "http://goo.gl/pxxZrg" source to field number 1 Then I see status message "No Timed Transcript"
        After I upload the transcripts file "uk_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        And I see value "pxxZrg" in the field "Default Timed Transcript"
        After saving the changes video captions should be visible
        After I edit the component I should see status message "Timed Transcript Found"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('http://goo.gl/pxxZrg', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'pxxZrg'))
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')

    def test_upload_subtitles_w_different_names4(self):
        """
        Scenario: Relative link: File name and name of subs are different
        Given I have created a Video component

        After i enter a "/gizmo.webm" source to field number 1 Then I see status message "No Timed Transcript"
        After I upload the transcripts file "uk_transcripts.srt" I see message "Timed Transcript Uploaded Successfully"
        And I see value "gizmo" in the field "Default Timed Transcript"
        After saving the changes video captions should be visible
        After I edit the component I should see status message "Timed Transcript Found"
        """
        self._create_video_component()
        self.edit_component()

        self.video.set_url_field('/gizmo.webm', 1)
        self.assertEqual(self.video.message('status'), 'No Timed Transcript')
        self.video.upload_transcript('uk_transcripts.srt')
        self.assertEqual(self.video.message('status'), 'Timed Transcript Uploaded Successfully')
        self.open_advanced_tab()
        self.assertTrue(self.video.verify_field_value('Default Timed Transcript', 'gizmo'))
        self.save_unit_settings()
        self.assertTrue(self.video.is_captions_visible())
        self.edit_component()
        self.assertEqual(self.video.message('status'), 'Timed Transcript Found')
