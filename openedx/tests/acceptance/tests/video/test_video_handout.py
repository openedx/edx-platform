# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Handout.
"""
from nose.plugins.attrib import attr
from openedx.tests.acceptance.tests.video.test_studio_video_module import CMSVideoBaseTest


@attr(shard=5)
class VideoHandoutTest(CMSVideoBaseTest):
    """
    CMS Video Handout Test Class
    """

    def setUp(self):
        super(VideoHandoutTest, self).setUp()

    def _create_course_unit_with_handout(self, handout_filename, save_settings=True):
        """
        Create a course with unit and also upload handout

        Arguments:
            handout_filename (str): handout file name to be uploaded
            save_settings (bool): save settings or not

        """
        self.navigate_to_course_unit()

        self.edit_component()

        self.open_advanced_tab()

        self.video.upload_handout(handout_filename)

        if save_settings:
            self.save_unit_settings()

    def test_handout_uploads_correctly(self):
        """
        Scenario: Handout uploading works correctly
        Given I have created a Video component with handout file "textbook.pdf"
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self._create_course_unit_with_handout('textbook.pdf')

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

    def test_handout_download_works_with_save(self):
        """
        Scenario: Handout downloading works correctly w/ preliminary saving
        Given I have created a Video component with handout file "textbook.pdf"
        And I save changes
        And I edit the component
        And I open tab "Advanced"
        And I can download handout file in editor with mime type "application/pdf"
        """
        self._create_course_unit_with_handout('textbook.pdf')

        self.edit_component()

        self.open_advanced_tab()

        self.assertEqual(self.video.download_handout('application/pdf', is_editor=True), (True, True))

    def test_handout_download_works_wo_save(self):
        """
        Scenario: Handout downloading works correctly w/o preliminary saving
        Given I have created a Video component with handout file "textbook.pdf"
        And I can download handout file in editor with mime type "application/pdf"
        """
        self._create_course_unit_with_handout('textbook.pdf', save_settings=False)

        self.assertEqual(self.video.download_handout('application/pdf', is_editor=True), (True, True))

    def test_handout_clearing_works_w_save(self):
        """
        Scenario: Handout clearing works correctly w/ preliminary saving
        Given I have created a Video component with handout file "textbook.pdf"
        And I save changes
        And I can download handout file with mime type "application/pdf"
        And I edit the component
        And I open tab "Advanced"
        And I clear handout
        And I save changes
        Then I do not see video button "handout"
        """
        self._create_course_unit_with_handout('textbook.pdf')

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

        self.edit_component()

        self.open_advanced_tab()

        self.video.clear_handout()

        self.save_unit_settings()

        self.assertFalse(self.video.is_handout_button_visible)

    def test_handout_clearing_works_wo_save(self):
        """
        Scenario: Handout clearing works correctly w/o preliminary saving
        Given I have created a Video component with handout file "asset.html"
        And I clear handout
        And I save changes
        Then I do not see video button "handout"
        """
        self._create_course_unit_with_handout('asset.html', save_settings=False)

        self.video.clear_handout()

        self.save_unit_settings()

        self.assertFalse(self.video.is_handout_button_visible)

    def test_handout_replace_w_save(self):
        """
        Scenario: User can easy replace the handout by another one w/ preliminary saving
        Given I have created a Video component with handout file "asset.html"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "text/html"
        And I edit the component
        And I open tab "Advanced"
        And I replace handout file by "textbook.pdf"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self._create_course_unit_with_handout('asset.html')

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('text/html'), (True, True))

        self.edit_component()

        self.open_advanced_tab()

        self.video.upload_handout('textbook.pdf')

        self.save_unit_settings()

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

    def test_handout_replace_wo_save(self):
        """
        Scenario: User can easy replace the handout by another one w/o preliminary saving
        Given I have created a Video component with handout file "asset.html"
        And I replace handout file by "textbook.pdf"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self._create_course_unit_with_handout('asset.html', save_settings=False)

        self.video.upload_handout('textbook.pdf')

        self.save_unit_settings()

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

    def test_handout_upload_and_clear_works(self):
        """
        Scenario: Upload file "A" -> Remove it -> Upload file "B"
        Given I have created a Video component with handout file "asset.html"
        And I clear handout
        And I upload handout file "textbook.pdf"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self._create_course_unit_with_handout('asset.html', save_settings=False)

        self.video.clear_handout()

        self.video.upload_handout('textbook.pdf')

        self.save_unit_settings()

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))
