"""
Acceptance Tests for Course Information
"""
from common.test.acceptance.pages.studio.course_info import CourseUpdatesPage
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.pages.studio.utils import type_in_codemirror

from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.index import DashboardPage


class UsersCanAddUpdatesTest(StudioCourseTest):
    """
    Series of Bok Choy Tests to test the Course Updates page
    """

    def _create_and_verify_update(self, message):
        """
        Helper method to create and verify and update based on the message.

        Arguments:
            message (str): Message to add to the update.
        """
        self.course_updates_page.visit()
        self.assertTrue(self.course_updates_page.is_new_update_button_present())
        self.course_updates_page.click_new_update_button()
        self.course_updates_page.submit_update(message)
        self.assertTrue(self.course_updates_page.is_first_update_message(message))

    def _create_handout(self, handout_message):
        self.course_updates_page.visit()
        self.assertTrue(self.course_updates_page.is_edit_handout_button_present())
        self.course_updates_page.click_edit_handout_button()
        self.course_updates_page.submit_handout(handout_message)

    def setUp(self, is_staff=False, test_xss=True):
        super(UsersCanAddUpdatesTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)
        self.course_updates_page = CourseUpdatesPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def test_course_updates_page_exists(self):
        """
        Scenario: User can access Course Updates Page
            Given I have opened a new course in Studio
            And I go to the course updates page
            When I visit the page
            Then I should see any course updates
            And I should see the new update button
        """
        self.course_updates_page.visit()
        self.course_updates_page.wait_for_page()
        self.assertTrue(self.course_updates_page.is_new_update_button_present)

    def test_new_course_update_is_present(self):
        """
          Scenario: Users can add updates
              Given I have opened a new course in Studio
              And I go to the course updates page
              When I add a new update with the text "Hello"
              Then I should see the update "Hello"
              And I see a "saving" notification
        """
        self._create_and_verify_update('Hello')

    def test_new_course_update_can_be_edited(self):
        """
        Scenario: Users can edit updates
            Given I have opened a new course in Studio
            And I go to the course updates page
            When I add a new update with the text "Hello"
            And I modify the text to "Goodbye"
            Then I should see the update "Goodbye"
        """
        self._create_and_verify_update('Hello')
        self.assertTrue(self.course_updates_page.is_edit_button_present())
        self.course_updates_page.click_edit_update_button()
        self.course_updates_page.submit_update('Goodbye')
        self.assertFalse(self.course_updates_page.is_first_update_message('Hello'))
        self.assertTrue(self.course_updates_page.is_first_update_message('Goodbye'))

    def test_delete_course_update(self):
        """
        Scenario: Users can delete updates
              Given I have opened a new course in Studio
              And I go to the course updates page
              And I add a new update with the text "Hello"
              And I delete the update
              And I confirm the prompt
              Then I should not see the update "Hello"
        """
        self._create_and_verify_update('Hello')
        self.course_updates_page.click_delete_update_button()
        self.assertTrue(self.course_updates_page.is_course_update_list_empty())

    def test_user_edit_date(self):
        """
        Scenario: Users can edit update dates
            Given I have opened a new course in Studio
            And I go to the course updates page
            And I add a new update with the text "Hello"
            When I edit the date to "06/01/13"
            Then I should see the date "June 1, 2013"
        """
        self._create_and_verify_update('Hello')
        self.course_updates_page.click_edit_update_button()
        self.course_updates_page.set_date('06/01/2013')
        self.course_updates_page.click_new_update_save_button()
        self.assertTrue(self.course_updates_page.is_first_update_date('June 1, 2013'))

    def test_outside_tag_preserved(self):
        """
        Scenario: Text outside of tags is preserved
            Given I have opened a new course in Studio
            And I go to the course updates page
            When I add a new update with the text "before <strong>middle</strong> after"
            Then I should see the update "before <strong>middle</strong> after"
            And when I reload the page
            Then I should see the update "before <strong>middle</strong> after"
        """
        self._create_and_verify_update('before <strong>middle</strong> after')
        self.course_updates_page.visit()
        self.assertTrue(self.course_updates_page.is_first_update_message('before <strong>middle</strong> after'))

    def test_asset_change_in_updates(self):
        """
        Scenario: Static links are rewritten when previewing a course update
           Given I have opened a new course in Studio
           And I go to the course updates page
           When I add a new update with the text "<img src='/static/my_img.jpg'/>"
           # Can only do partial text matches because of the quotes with in quotes (and regexp step matching).
           Then I should see the asset update to "my_img.jpg"
           And I change the update from "/static/my_img.jpg" to "<img src='/static/modified.jpg'/>"
           Then I should see the asset update to "modified.jpg"
           And when I reload the page
           Then I should see the asset update to "modified.jpg"
        """
        self.course_updates_page.visit()
        self.assertTrue(self.course_updates_page.is_new_update_button_present())
        self.course_updates_page.click_new_update_button()
        self.course_updates_page.submit_update("<img src='/static/my_img.jpg'/>")
        self.assertTrue(self.course_updates_page.first_update_contains_html("my_img.jpg"))
        self.course_updates_page.click_edit_update_button()
        self.course_updates_page.submit_update("<img src='/static/modified.jpg'/>")
        self.assertFalse(self.course_updates_page.first_update_contains_html("my_img.jpg"))
        self.assertTrue(self.course_updates_page.first_update_contains_html("modified.jpg"))
        self.course_updates_page.visit()
        self.assertTrue(self.course_updates_page.first_update_contains_html("modified.jpg"))

    def test_handout_message_present(self):
        """
        Scenario: Users can add handouts
            Given I have opened a new course in Studio
            And I go to the course updates page
            When I add a new handout with the text "Hello"
            Then I should see the handout "Hello"
            And I see a "saving" notification
        """
        self._create_handout('Hello')
        self.assertTrue(self.course_updates_page.is_first_handout('Hello'))

    def test_bad_html_handout_cannot_be_saved(self):
        """
        Scenario: Users cannot hadnout with bad html
            Given I have opened a new course in Studio
            And I go to the course updates page
            And I add a new handout with text '<p><a href=>[LINK TEXT]</a></p>'
            Then I see the handout error text
            And edit handout with text '<p><a href="https://www.google.com.pk/">home</a></p>'
            Then I should see the saved handout
            And I see a "saving" notification
        """
        self.course_updates_page.visit()
        self.assertTrue(self.course_updates_page.is_edit_handout_button_present())
        self.course_updates_page.click_edit_handout_button()
        type_in_codemirror(self.course_updates_page, 0, '<p><a href=>[LINK TEXT]</a></p>')
        self.course_updates_page.click_save_handout_button()
        self.assertEqual(
            self.course_updates_page.get_handout_error_text(),
            'There is invalid code in your content. Please check to make sure it is valid HTML.'
        )
        self.assertTrue(self.course_updates_page.check_save_handout_button_enabled())
        type_in_codemirror(self.course_updates_page, 0, '<p><a href="https://www.google.com.pk/">home</a></p>')
        self.assertFalse(self.course_updates_page.check_save_handout_button_enabled())
        self.course_updates_page.click_new_handout_save_button()
        self.assertEqual(
            self.course_updates_page.get_new_handout_link(),
            'https://www.google.com.pk/'
        )
        self.course_updates_page.refresh_and_wait_for_load()
        self.assertEqual(self.course_updates_page.get_new_handout_link(), 'https://www.google.com.pk/')

    def test_static_links_are_rewritten(self):
        """
        Scenario: Static links are rewritten when previewing a course handout
            Given I have opened a new course in Studio
            And I go to the course updates page
            When I add a new handout with the text "<ol><img src="/static/my_img.jpg"/></ol>"
            Then I should see the asset handout to "my_img.jpg"
            And I change the handout from "/static/my_img.jpg" to "<img src='/static/modified.jpg'/>"
            Then I should see the asset handout to "modified.jpg"
            And when I reload the page
            Then I should see the asset handout to "modified.jpg"
        """
        self._create_handout('<ol><img src="/static/my_img.jpg"/></ol>')
        image_source = self.course_updates_page.get_image_src()
        self.assertIn('my_img.jpg', image_source)
        self.course_updates_page.click_edit_handout_button()
        self.course_updates_page.submit_handout('<img src="/static/modified.jpg"/>')
        self.course_updates_page.refresh_and_wait_for_load()
        modified_image_source = self.course_updates_page.get_image_src()
        self.assertIn('modified.jpg', modified_image_source)
