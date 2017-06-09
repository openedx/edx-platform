"""
Acceptance tests for course in studio
"""
from nose.plugins.attrib import attr

from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage

from common.test.acceptance.pages.studio.users import CourseTeamPage
from common.test.acceptance.pages.studio.index import DashboardPage


@attr(shard=2)
class CourseTeamPageTest(StudioCourseTest):
    """ As a course author, I want to be able to add others to my team """
    def _make_user(self, username):
        """ Registers user and returns user representation dictionary as expected by `log_in` function """
        user = {
            'username': username,
            'email': username + "@example.com",
            'password': username + '123'
        }
        AutoAuthPage(
            self.browser, no_login=True,
            username=user.get('username'), email=user.get('email'), password=user.get('password')
        ).visit()
        return user

    def _update_user(self, user_info):
        """
        Update user with provided `user_info`

        Arguments:
            `user_info`: dictionary containing values of attributes to be updated
        """
        AutoAuthPage(
            self.browser, no_login=True, **user_info
        ).visit()

    def setUp(self, is_staff=False):
        """
        Install a course with no content using a fixture.
        """
        super(CourseTeamPageTest, self).setUp(is_staff)

        self.other_user = self._make_user('other')
        self.dashboard_page = DashboardPage(self.browser)
        self.page = CourseTeamPage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )
        self._go_to_course_team_page()

    def _go_to_course_team_page(self):
        """ Opens Course Team page """
        self.page.visit()
        self.page.wait_until_no_loading_indicator()

    def _refresh_page(self):
        """
        Reload the page.
        """
        self.page = CourseTeamPage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )
        self._go_to_course_team_page()

    def _assert_current_course(self, visible=True):
        """ Checks if current course is accessible to current user """
        self.dashboard_page.visit()
        courses = self.dashboard_page.list_courses()

        def check_course_equality(course1, course2):
            """ Compares to course dictionaries using org, number and run as keys"""
            return (
                course1['org'] == course2['display_organization'] and
                course1['number'] == course2['display_coursenumber'] and
                course1['run'] == course2['run']
            )

        actual_visible = any((check_course_equality(course, self.course_info) for course in courses))

        self.assertEqual(actual_visible, visible)

    def _assert_user_present(self, user, present=True):
        """ Checks if specified user present on Course Team page """
        if present:
            self.page.wait_for(
                lambda: user.get('username') in self.page.usernames,
                description="Wait for user to be present"
            )
        else:
            self.page.wait_for(
                lambda: user.get('username') not in self.page.usernames,
                description="Wait for user to be absent"
            )

    def _should_see_dialog(self, dialog_type, dialog_message):
        """ Asserts dialog with specified message is shown """
        self.page.modal_dialog_visible(dialog_type)
        self.assertIn(dialog_message, self.page.modal_dialog_text(dialog_type))

    def _assert_is_staff(self, user, can_manage=True):
        """ Checks if user have staff permissions, can be promoted and can't be demoted """
        self.assertIn("staff", user.role_label.lower())
        if can_manage:
            self.assertTrue(user.can_promote)
            self.assertFalse(user.can_demote)
            self.assertIn("Add Admin Access", user.promote_button_text)

    def _assert_is_admin(self, user):
        """ Checks if user have admin permissions, can't be promoted and can be demoted """
        self.assertIn("admin", user.role_label.lower())
        self.assertFalse(user.can_promote)
        self.assertTrue(user.can_demote)
        self.assertIn("Remove Admin Access", user.demote_button_text)

    def _assert_can_manage_users(self):
        """ Checks if current user can manage course team """
        self.assertTrue(self.page.has_add_button)
        for user in self.page.users:
            self.assertTrue(user.can_promote or user.can_demote)  # depending on actual user role
            self.assertTrue(user.can_delete)

    def _assert_can_not_manage_users(self):
        """ Checks if current user can't manage course team """
        self.assertFalse(self.page.has_add_button)
        for user in self.page.users:
            self.assertFalse(user.can_promote)
            self.assertFalse(user.can_demote)
            self.assertFalse(user.can_delete)

    def test_admins_can_add_other_users(self):
        """
        Scenario: Admins can add other users
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add other user to the course team
        And other user logs in
        Then he does see the course on her page
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)
        self.log_in(self.other_user)
        self._assert_current_course(visible=True)

    def test_added_users_cannot_add_or_delete_other_users(self):
        """
        Scenario: Added users cannot delete or add other users
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add other user to the course team
        And other user logs in
        And he selects the new course
        And he views the course team settings
        Then he cannot manage users
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)

        self.log_in(self.other_user)
        self._assert_current_course(visible=True)
        self._go_to_course_team_page()

        bob = self.page.get_user(self.other_user.get('email'))
        self.assertTrue(bob.is_current_user)
        self.assertFalse(self.page.has_add_button)

        self._assert_can_not_manage_users()

    def test_admins_can_delete_other_users(self):
        """
        Scenario: Admins can delete other users
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add other user to the course team
        And I delete other user from the course team
        And other user logs in
        Then he does not see the course on her page
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)
        self.page.delete_user_from_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=False)

        self.log_in(self.other_user)
        self._assert_current_course(visible=False)

    def test_admins_can_delete_other_inactive_users(self):
        """
        Scenario: Admins can delete other inactive users
        Given I have opened a new course in Studio
        And I am viewing the course team settings.
        When I add other user to the course team,
        And then delete that other user from the course team.
        And other user logs in
        Then he/she does not see the course on page
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)

        # inactivate user
        user_info = {
            'username': self.other_user.get('username'),
            'email': self.other_user.get('email'),
            'password': self.other_user.get('password'),
            'is_active': False
        }
        self._update_user(user_info)

        # go to course team page to perform delete operation
        self._go_to_course_team_page()
        self.page.delete_user_from_course(self.other_user.get('email'))

        self._assert_user_present(self.other_user, present=False)

    def test_admins_cannot_add_users_that_do_not_exist(self):
        """
        Scenario: Admins cannot add users that do not exist
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add "dennis" to the course team
        Then I should see "Could not find user by email address" somewhere on the page
        """
        self.page.add_user_to_course("dennis@example.com")
        self._should_see_dialog('error', "Could not find user by email address")

    def test_admins_should_be_able_to_make_other_people_into_admins(self):
        """
        Scenario: Admins should be able to make other people into admins
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        And I add other user to the course team
        When I make other user a course team admin
        And other user logs in
        And he selects the new course
        And he views the course team settings
        Then other user should be marked as an admin
        And he can manage users
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)

        other = self.page.get_user(self.other_user.get('email'))
        self._assert_is_staff(other)
        other.click_promote()
        self._refresh_page()
        self._assert_is_admin(other)

        self.log_in(self.other_user)
        self._go_to_course_team_page()
        other = self.page.get_user(self.other_user.get('email'))
        self.assertTrue(other.is_current_user)
        self._assert_can_manage_users()

    def test_admins_should_be_able_to_remove_other_admins(self):
        """
        Scenario: Admins should be able to remove other admins
        Given I have opened a new course in Studio
        And I grant admin rights to other user
        Then he can add, delete, promote and demote users
        And I am viewing the course team settings
        When I remove admin rights from other user
        And other user logs in
        And he selects the new course
        And he views the course team settings
        Then other user should not be marked as an admin
        And he cannot manage users
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)

        other = self.page.get_user(self.other_user.get('email'))
        self._assert_is_staff(other)
        other.click_promote()
        self._refresh_page()
        other = self.page.get_user(self.other_user.get('email'))
        self._assert_is_admin(other)

        # precondition check - frank is an admin and can add/delete/promote/demote users
        self.log_in(self.other_user)
        self._go_to_course_team_page()
        other = self.page.get_user(self.other_user.get('email'))
        self.assertTrue(other.is_current_user)
        self._assert_can_manage_users()

        self.log_in(self.user)
        self._go_to_course_team_page()
        other = self.page.get_user(self.other_user.get('email'))
        other.click_demote()
        self._refresh_page()
        other = self.page.get_user(self.other_user.get('email'))
        self._assert_is_staff(other)

        self.log_in(self.other_user)
        self._go_to_course_team_page()
        other = self.page.get_user(self.other_user.get('email'))
        self.assertTrue(other.is_current_user)
        self._assert_can_not_manage_users()

    def test_admins_should_be_able_to_remove_themself_if_other_admin_exists(self):
        """
        Scenario: Admins should be able to give course ownership to someone else
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        And I'm the only course admin
        Then I cannot delete or demote myself
        When I add other user to the course team
        And I make other user a course team admin
        Then I can delete or demote myself
        When I delete myself from the course team
        And I am logged into studio
        Then I do not see the course on my page
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)

        current = self.page.get_user(self.user.get('email'))
        self.assertFalse(current.can_demote)
        self.assertFalse(current.can_delete)
        self.assertIn("Promote another member to Admin to remove your admin rights", current.no_change_warning_text)

        other = self.page.get_user(self.other_user.get('email'))
        other.click_promote()
        self._refresh_page()
        other = self.page.get_user(self.other_user.get('email'))
        self._assert_is_admin(other)

        current = self.page.get_user(self.user.get('email'))
        self.assertTrue(current.can_demote)
        self.assertTrue(current.can_delete)
        current.click_delete()

        self.log_in(self.user)
        self._assert_current_course(visible=False)

    def test_admins_should_be_able_to_give_course_ownership_to_someone_else(self):
        """
        Scenario: Admins should be able to give course ownership to someone else
        Given I have opened a new course in Studio
        And I am viewing the course team settings
        When I add other user to the course team
        And I make other user a course team admin
        When I remove admin rights from myself
        Then I should not be marked as an admin
        And I cannot manage users
        And I cannot make myself a course team admin
        When other user logs in
        And he selects the new course
        And he views the course team settings
        And he deletes me from the course team
        And I am logged into studio
        Then I do not see the course on my page
        """
        self.page.add_user_to_course(self.other_user.get('email'))
        self._assert_user_present(self.other_user, present=True)

        current = self.page.get_user(self.user.get('email'))
        self.assertFalse(current.can_demote)
        self.assertFalse(current.can_delete)
        self.assertIn("Promote another member to Admin to remove your admin rights", current.no_change_warning_text)

        other = self.page.get_user(self.other_user.get('email'))
        other.click_promote()
        self._refresh_page()

        other = self.page.get_user(self.other_user.get('email'))
        self._assert_is_admin(other)

        current = self.page.get_user(self.user.get('email'))
        self.assertTrue(current.can_demote)
        self.assertTrue(current.can_delete)
        current.click_demote()
        self._refresh_page()
        current = self.page.get_user(self.user.get('email'))
        self._assert_is_staff(current, can_manage=False)
        self._assert_can_not_manage_users()
        self.assertFalse(current.can_promote)

        self.log_in(self.other_user)
        self._go_to_course_team_page()

        current = self.page.get_user(self.user.get('email'))
        current.click_delete()
        self._refresh_page()
        self._assert_user_present(self.user, present=False)

        self.log_in(self.user)
        self._assert_current_course(visible=False)
