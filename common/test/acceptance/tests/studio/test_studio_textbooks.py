"""
Acceptance tests for Studio related to the textbooks.
"""
from common.test.acceptance.pages.lms.textbook_view import TextbookViewPage
from common.test.acceptance.pages.studio.textbook_upload import TextbookUploadPage
from common.test.acceptance.tests.helpers import disable_animations
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from openedx.core.lib.tests import attr


class TextbooksTest(StudioCourseTest):
    """
    Test that textbook functionality is working properly on studio side
    """
    def setUp(self, is_staff=True):  # pylint: disable=arguments-differ
        """
        Install a course with no content using a fixture.
        """
        super(TextbooksTest, self).setUp(is_staff)
        self.textbook_upload_page = TextbookUploadPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.textbook_upload_page.visit()
        disable_animations(self)

        self.textbook_view_page = TextbookViewPage(self.browser, self.course_id)

    def _assert_textbook_data(self, textbook_data):
        """
        Asserts the textbook data on textbook page
        """
        textbook_name = self.textbook_upload_page.textbook_name
        self.assertEqual(textbook_data['textbook_name'], textbook_name)
        self.textbook_upload_page.toggle_chapters()
        number_of_chapters = self.textbook_upload_page.number_of_chapters
        self.assertEqual(2, number_of_chapters)
        first_chapter_name = self.textbook_upload_page.get_chapter_name(0)
        second_chapter_name = self.textbook_upload_page.get_chapter_name(1)
        self.assertEqual(textbook_data['first_chapter'], first_chapter_name)
        self.assertEqual(textbook_data['second_chapter'], second_chapter_name)
        first_asset_name = self.textbook_upload_page.get_asset_name(0)
        second_asset_name = self.textbook_upload_page.get_asset_name(1)
        self.assertEqual(textbook_data['first_asset'], first_asset_name)
        self.assertEqual(textbook_data['second_asset'], second_asset_name)

    @attr(shard=9)
    def test_create_first_book_message(self):
        """
        Scenario: A message is displayed on the textbooks page when there are no uploaded textbooks
        Given that I am viewing the Textbooks page in Studio
        And I have not yet uploaded a textbook
        Then I see a message stating that I have not uploaded any textbooks
        """
        message = self.textbook_upload_page.get_element_text('.wrapper-content .no-textbook-content')
        self.assertIn("You haven't added any textbooks", message)

    @attr(shard=9)
    def test_new_textbook_upload(self):
        """
        Scenario: View Live link for textbook is correctly populated
        Given that I am viewing the Textbooks page in Studio
        And I have uploaded a PDF textbook and save the new textbook information
        Then the "View Live" link contains a link to the textbook in the LMS
        """
        self.textbook_upload_page.upload_new_textbook()
        self.assertTrue(self.textbook_upload_page.is_view_live_link_worked())

    @attr('a11y')
    def test_textbook_page_a11y(self):
        """
        Uploads a new textbook
        Runs an accessibility test on the textbook page in lms
        """
        self.textbook_upload_page.upload_new_textbook()
        self.textbook_view_page.visit()

        self.textbook_view_page.a11y_audit.config.set_rules({
            'ignore': [
                'section',  # AC-503
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
            ],
        })
        self.textbook_view_page.a11y_audit.check_for_accessibility_errors()

    @attr('a11y')
    def test_pdf_viewer_a11y(self):
        """
        Uploads a new textbook
        Runs an accessibility test on the pdf viewer frame in lms
        """
        self.textbook_upload_page.upload_new_textbook()
        self.textbook_view_page.visit()

        self.textbook_view_page.switch_to_pdf_frame(self)
        self.textbook_view_page.a11y_audit.config.set_scope({
            'exclude': [
                '#viewer',  # PDF viewer (vendor file)
            ]
        })
        self.textbook_view_page.a11y_audit.config.set_rules({
            'ignore': [
                'color-contrast',  # will always fail because pdf.js converts pdf to divs with transparent text
            ],
        })
        self.textbook_view_page.a11y_audit.check_for_accessibility_errors()

    def test_create_textbooks_with_multiple_chapters(self):
        """
        Scenario: Create a textbook with multiple chapters
            Given I have opened a new course in Studio
            And I go to the textbooks page
            And I name my textbook "History"
            And I name the first chapter "Britain"
            And I type in "britain.pdf" for the first chapter asset
            And I click Add a Chapter
            And I name the second chapter "America"
            And I type in "america.pdf" for the second chapter asset
            And I save the textbook
            Then I should see a textbook named "History" with 2 chapters
            And I click the textbook chapters
            Then I should see a textbook named "History" with 2 chapters
            And the first chapter should be named "Britain"
            And the first chapter should have an asset called "britain.pdf"
            And the second chapter should be named "America"
            And the second chapter should have an asset called "america.pdf"
            And I reload the page
            Then I should see a textbook named "History" with 2 chapters
            And I click the textbook chapters
            Then I should see a textbook named "History" with 2 chapters
            And the first chapter should be named "Britain"
            And the first chapter should have an asset called "britain.pdf"
            And the second chapter should be named "America"
            And the second chapter should have an asset called "america.pdf"
        """
        textbook_data = {
            'textbook_name': 'History',
            'first_chapter': 'Britain',
            'first_asset': 'britain.pdf',
            'second_chapter': 'America',
            'second_asset': 'america.pdf'
        }
        self.textbook_upload_page.set_textbook_name(textbook_data['textbook_name'])
        self.textbook_upload_page.fill_chapter_name('first', textbook_data['first_chapter'])
        self.textbook_upload_page.fill_chapter_asset('first', textbook_data['first_asset'])
        self.textbook_upload_page.submit_chapter()
        self.textbook_upload_page.fill_chapter_name('second', textbook_data['second_chapter'])
        self.textbook_upload_page.fill_chapter_asset('second', textbook_data['second_asset'])
        self.textbook_upload_page.click_textbook_submit_button()
        self._assert_textbook_data(textbook_data)
        self.textbook_upload_page.refresh_and_wait_for_load()
        self.textbook_upload_page.toggle_chapters()
        self._assert_textbook_data(textbook_data)
