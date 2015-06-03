"""
Acceptance tests for Studio related to the textbook.
"""
from acceptance.tests.studio.base_studio_test import StudioCourseTest
from ...pages.studio.textbooks import TextbooksPage


class TextbookTest(StudioCourseTest):
    """
    Test that textbook functionality is working properly on studio side
    """
    def setUp(self, is_staff=True):
        """
        Install a course with no content using a fixture.
        """
        super(TextbookTest, self).setUp(is_staff)
        self.textbook_page = TextbooksPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.textbook_page.visit()

    def test_create_first_book_message(self):
        """
        check that create first book message is showing when no book is uploaded yet
        """
        message = self.textbook_page.get_element_text('.wrapper-content .no-textbook-content')
        self.assertIn("You haven't added any textbooks", message)

    def test_new_textbook_upload(self):
        """
        Test that the textbook will not go to 404 on viewing it on lms
        """
        self.textbook_page.open_add_textbook_form()
        self.textbook_page.upload_pdf_file('textbook.pdf')
        self.textbook_page.set_input_field_value('.edit-textbook #textbook-name-input', 'book_1')
        self.textbook_page.set_input_field_value('.edit-textbook #chapter1-name', 'chapter_1')
        self.textbook_page.click_textbook_submit_button('book_1')
        self.assertTrue(self.textbook_page.is_view_live_link_worked())
