"""
Acceptance tests for Studio related to the textbooks.
"""
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.pages.studio.textbook_upload import TextbookUploadPage
from common.test.acceptance.pages.lms.textbook_view import TextbookViewPage
from common.test.acceptance.tests.helpers import disable_animations
from nose.plugins.attrib import attr


@attr(shard=2)
class TextbooksTest(StudioCourseTest):
    """
    Test that textbook functionality is working properly on studio side
    """
    def setUp(self, is_staff=True):
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

    def test_create_first_book_message(self):
        """
        Scenario: A message is displayed on the textbooks page when there are no uploaded textbooks
        Given that I am viewing the Textbooks page in Studio
        And I have not yet uploaded a textbook
        Then I see a message stating that I have not uploaded any textbooks
        """
        message = self.textbook_upload_page.get_element_text('.wrapper-content .no-textbook-content')
        self.assertIn("You haven't added any textbooks", message)

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
                'skip-link',  # AC-501
                'section'  # AC-503
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
                'html-lang',  # AC-504
                'meta-viewport',  # AC-505
                'skip-link',  # AC-506
            ],
        })
        self.textbook_view_page.a11y_audit.check_for_accessibility_errors()
