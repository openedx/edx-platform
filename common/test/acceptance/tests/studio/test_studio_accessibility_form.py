"""
Bok-choy tests for the Studio Accessibility Feedback page.
"""
import ddt

from common.test.acceptance.pages.studio.index import AccessibilityPage
from common.test.acceptance.tests.helpers import AcceptanceTest


@ddt.ddt
class AccessibilityPageTest(AcceptanceTest):
    """
    Test that a user can access the page and submit studio accessibility feedback.
    """
    shard = 21

    def setUp(self):
        """
        Load the helper for the accessibility page.
        """
        super(AccessibilityPageTest, self).setUp()
        self.accessibility_page = AccessibilityPage(self.browser)

    def test_page_loads(self):
        """
        Test if the page loads and that there is a header and input elements.
        """
        self.accessibility_page.visit()
        self.assertTrue(self.accessibility_page.header_text_on_page())

    def test_successful_submit(self):
        """
        Test filling out the accessibility feedback form out and submitting.
        """
        self.accessibility_page.visit()
        self.accessibility_page.fill_form(email='bokchoy@edx.org', name='Bok-choy', message='I\'m testing you.')
        self.accessibility_page.submit_form()

    @ddt.data(
        ('email', 'Enter a valid email address', '', 'Bok-choy', 'I\'m testing you.'),
        ('fullName', 'Enter a name', 'bokchoy@edx.org', '', 'I\'m testing you.'),
        ('message', 'Enter a message', 'bokchoy@edx.org', 'Bok-choy', ''),
    )
    @ddt.unpack
    def test_error_submit(self, field_missing, error_message_text, email, name, message):
        """
        Test filling out the accessibility feedback form out with each field missing and then submitting.
        """
        self.accessibility_page.visit()
        self.accessibility_page.fill_form(email=email, name=name, message=message)
        self.accessibility_page.error_message_is_shown_with_text(field_missing, text=error_message_text)
        self.accessibility_page.submit_form()
        self.accessibility_page.alert_has_text(error_message_text)

    def test_error_messages(self):
        self.accessibility_page.visit()
        self.check_error_message('email', 'Enter a valid email address')
        self.check_error_message('fullName', 'Enter a name')
        self.check_error_message('message', 'Enter a message', field_type='textarea')

    def check_error_message(self, field_id, error_message_text, field_type='input'):
        self.accessibility_page.leave_field_blank(field_id, field_type=field_type)
        self.accessibility_page.error_message_is_shown_with_text(field_id, text=error_message_text)
