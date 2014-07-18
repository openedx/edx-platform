# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Editor.
"""

from .test_studio_video_module import CMSVideoBaseTest


class VideoEditorTest(CMSVideoBaseTest):
    """
    CMS Video Editor Test Class
    """

    def setUp(self):
        super(VideoEditorTest, self).setUp()

    def _create_video_component(self, subtitles=False):
        """
        Create a video component and navigate to unit page

        Arguments:
            subtitles (bool): Upload subtitles or not

        """
        if subtitles:
            self.assets.append('subs_OEoXaMPEzfM.srt.sjson')

        self.navigate_to_course_unit()

    def test_default_settings(self):
        """
        Scenario: User can view Video metadata
        Given I have created a Video component
        And I edit the component
        Then I see the correct video settings and default values
        """
        self._create_video_component()

        self.edit_component()

        self.assertTrue(self.video.verify_settings())

    def test_modify_video_display_name(self):
        """
        Scenario: User can modify Video display name
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        Then I can modify video display name
        And my video display name change is persisted on save
        """
        self._create_video_component()

        self.edit_component()

        self.open_advanced_tab()

        self.video.set_field_value('Component Display Name', 'Transformers')

        self.save_unit_settings()

        self.edit_component()

        self.open_advanced_tab()

        self.assertTrue(self.video.verify_field_value('Component Display Name', 'Transformers'))
