"""
Acceptance tests for Content Libraries in Studio
"""


from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.studio.library import LibraryEditPage
from common.test.acceptance.pages.studio.users import LibraryUsersPage
from common.test.acceptance.tests.studio.base_studio_test import StudioLibraryTest
from openedx.core.lib.tests import attr


@attr(shard=21)
class LibraryUsersPageTest(StudioLibraryTest):
    """
    Test the functionality of the library "Instructor Access" page.
    """
    def setUp(self):
        super(LibraryUsersPageTest, self).setUp()

        # Create a second user for use in these tests:
        AutoAuthPage(self.browser, username="second", email="second@example.com", no_login=True).visit()

        self.page = LibraryUsersPage(self.browser, self.library_key)
        self.page.visit()

    def _refresh_page(self):
        """
        Reload the page.
        """
        self.page = LibraryUsersPage(self.browser, self.library_key)
        self.page.visit()

    def test_user_management(self):
        """
        Scenario: Ensure that we can edit the permissions of users.
        Given I have a library in Studio where I am the only admin
        assigned (which is the default for a newly-created library)
        And I navigate to Library "Instructor Access" Page in Studio
        Then there should be one user listed (myself), and I must
        not be able to remove myself or my instructor privilege.

        When I click Add Instructor
        Then I see a form to complete
        When I complete the form and submit it
        Then I can see the new user is listed as a "User" of the library

        When I click to Add Staff permissions to the new user
        Then I can see the new user has staff permissions and that I am now
        able to promote them to an Admin or remove their staff permissions.

        When I click to Add Admin permissions to the new user
        Then I can see the new user has admin permissions and that I can now
        remove Admin permissions from either user.
        """
        def check_is_only_admin(user):
            """
            Ensure user is an admin user and cannot be removed.
            (There must always be at least one admin user.)
            """
            self.assertIn("admin", user.role_label.lower())
            self.assertFalse(user.can_promote)
            self.assertFalse(user.can_demote)
            self.assertFalse(user.can_delete)
            self.assertTrue(user.has_no_change_warning)
            self.assertIn("Promote another member to Admin to remove your admin rights", user.no_change_warning_text)

        self.assertEqual(len(self.page.users), 1)
        user = self.page.users[0]
        self.assertTrue(user.is_current_user)
        check_is_only_admin(user)

        # Add a new user:

        self.assertTrue(self.page.has_add_button)
        self.assertFalse(self.page.new_user_form_visible)
        self.page.click_add_button()
        self.assertTrue(self.page.new_user_form_visible)
        self.page.set_new_user_email('second@example.com')
        self.page.click_submit_new_user_form()

        # Check the new user's listing:

        def get_two_users():
            """
            Expect two users to be listed, one being me, and another user.
            Returns me, them
            """
            users = self.page.users
            self.assertEqual(len(users), 2)
            self.assertEqual(len([u for u in users if u.is_current_user]), 1)
            if users[0].is_current_user:
                return users[0], users[1]
            else:
                return users[1], users[0]

        self._refresh_page()
        user_me, them = get_two_users()
        check_is_only_admin(user_me)

        self.assertIn("user", them.role_label.lower())
        self.assertTrue(them.can_promote)
        self.assertIn("Add Staff Access", them.promote_button_text)
        self.assertFalse(them.can_demote)
        self.assertTrue(them.can_delete)
        self.assertFalse(them.has_no_change_warning)

        # Add Staff permissions to the new user:

        them.click_promote()
        self._refresh_page()
        user_me, them = get_two_users()
        check_is_only_admin(user_me)

        self.assertIn("staff", them.role_label.lower())
        self.assertTrue(them.can_promote)
        self.assertIn("Add Admin Access", them.promote_button_text)
        self.assertTrue(them.can_demote)
        self.assertIn("Remove Staff Access", them.demote_button_text)
        self.assertTrue(them.can_delete)
        self.assertFalse(them.has_no_change_warning)

        # Add Admin permissions to the new user:

        them.click_promote()
        self._refresh_page()
        user_me, them = get_two_users()
        self.assertIn("admin", user_me.role_label.lower())
        self.assertFalse(user_me.can_promote)
        self.assertTrue(user_me.can_demote)
        self.assertTrue(user_me.can_delete)
        self.assertFalse(user_me.has_no_change_warning)

        self.assertIn("admin", them.role_label.lower())
        self.assertFalse(them.can_promote)
        self.assertTrue(them.can_demote)
        self.assertIn("Remove Admin Access", them.demote_button_text)
        self.assertTrue(them.can_delete)
        self.assertFalse(them.has_no_change_warning)

        # Delete the new user:

        them.click_delete()
        self._refresh_page()
        self.assertEqual(len(self.page.users), 1)
        user = self.page.users[0]
        self.assertTrue(user.is_current_user)


@attr('a11y')
class StudioLibraryA11yTest(StudioLibraryTest):
    """
    Class to test Studio pages accessibility.
    """

    def test_lib_edit_page_a11y(self):
        """
        Check accessibility of LibraryEditPage.
        """
        lib_page = LibraryEditPage(self.browser, self.library_key)
        lib_page.visit()
        lib_page.wait_until_ready()

        lib_page.a11y_audit.config.set_rules({
            "ignore": [
                'link-href',  # TODO: AC-590
                'duplicate-id-aria',  # TODO: AC-940
                'heading-order',  # TODO: AC-933
                'landmark-complementary-is-top-level',  # TODO: AC-939
                'region'  # TODO: AC-932
            ],
        })

        lib_page.a11y_audit.check_for_accessibility_errors()
