"""
Acceptance tests for Content Libraries in Studio
"""
from ddt import ddt, data
from nose.plugins.attrib import attr
from flaky import flaky

from common.test.acceptance.tests.studio.base_studio_test import StudioLibraryTest
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage
from common.test.acceptance.pages.studio.utils import add_component
from common.test.acceptance.pages.studio.library import LibraryEditPage
from common.test.acceptance.pages.studio.users import LibraryUsersPage


@attr(shard=2)
@ddt
class LibraryEditPageTest(StudioLibraryTest):
    """
    Test the functionality of the library edit page.
    """
    def setUp(self):
        """
        Ensure a library exists and navigate to the library edit page.
        """
        super(LibraryEditPageTest, self).setUp()
        self.lib_page = LibraryEditPage(self.browser, self.library_key)
        self.lib_page.visit()
        self.lib_page.wait_until_ready()

    def test_page_header(self):
        """
        Scenario: Ensure that the library's name is displayed in the header and title.
        Given I have a library in Studio
        And I navigate to Library Page in Studio
        Then I can see library name in page header title
        And I can see library name in browser page title
        """
        self.assertIn(self.library_info['display_name'], self.lib_page.get_header_title())
        self.assertIn(self.library_info['display_name'], self.browser.title)

    def test_add_duplicate_delete_actions(self):
        """
        Scenario: Ensure that we can add an HTML block, duplicate it, then delete the original.
        Given I have a library in Studio with no XBlocks
        And I navigate to Library Page in Studio
        Then there are no XBlocks displayed
        When I add Text XBlock
        Then one XBlock is displayed
        When I duplicate first XBlock
        Then two XBlocks are displayed
        And those XBlocks locators' are different
        When I delete first XBlock
        Then one XBlock is displayed
        And displayed XBlock are second one
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)

        # Create a new block:
        add_component(self.lib_page, "html", "Text")
        self.assertEqual(len(self.lib_page.xblocks), 1)
        first_block_id = self.lib_page.xblocks[0].locator

        # Duplicate the block:
        self.lib_page.click_duplicate_button(first_block_id)
        self.assertEqual(len(self.lib_page.xblocks), 2)
        second_block_id = self.lib_page.xblocks[1].locator
        self.assertNotEqual(first_block_id, second_block_id)

        # Delete the first block:
        self.lib_page.click_delete_button(first_block_id, confirm=True)
        self.assertEqual(len(self.lib_page.xblocks), 1)
        self.assertEqual(self.lib_page.xblocks[0].locator, second_block_id)

    def test_no_edit_visibility_button(self):
        """
        Scenario: Ensure that library xblocks do not have 'edit visibility' buttons.
        Given I have a library in Studio with no XBlocks
        And I navigate to Library Page in Studio
        When I add Text XBlock
        Then one XBlock is displayed
        And no 'edit visibility' button is shown
        """
        add_component(self.lib_page, "html", "Text")
        self.assertFalse(self.lib_page.xblocks[0].has_edit_visibility_button)

    def test_add_edit_xblock(self):
        """
        Scenario: Ensure that we can add an XBlock, edit it, then see the resulting changes.
        Given I have a library in Studio with no XBlocks
        And I navigate to Library Page in Studio
        Then there are no XBlocks displayed
        When I add Multiple Choice XBlock
        Then one XBlock is displayed
        When I edit first XBlock
        And I go to basic tab
        And set it's text to a fairly trivial question about Battlestar Galactica
        And save XBlock
        Then one XBlock is displayed
        And first XBlock student content contains at least part of text I set
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        # Create a new problem block:
        add_component(self.lib_page, "problem", "Multiple Choice")
        self.assertEqual(len(self.lib_page.xblocks), 1)
        problem_block = self.lib_page.xblocks[0]
        # Edit it:
        problem_block.edit()
        problem_block.open_basic_tab()
        problem_block.set_codemirror_text(
            """
            >>Who is "Starbuck"?<<
             (x) Kara Thrace
             ( ) William Adama
             ( ) Laura Roslin
             ( ) Lee Adama
             ( ) Gaius Baltar
            """
        )
        problem_block.save_settings()
        # Check that the save worked:
        self.assertEqual(len(self.lib_page.xblocks), 1)
        problem_block = self.lib_page.xblocks[0]
        self.assertIn("Laura Roslin", problem_block.author_content)

    def test_no_discussion_button(self):
        """
        Ensure the UI is not loaded for adding discussions.
        """
        self.assertFalse(self.browser.find_elements_by_css_selector('span.large-discussion-icon'))

    def test_library_pagination(self):
        """
        Scenario: Ensure that adding several XBlocks to a library results in pagination.
        Given that I have a library in Studio with no XBlocks
        And I create 10 Multiple Choice XBlocks
        Then 10 are displayed.
        When I add one more Multiple Choice XBlock
        Then 1 XBlock will be displayed
        When I delete that XBlock
        Then 10 are displayed.
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        for _ in range(10):
            add_component(self.lib_page, "problem", "Multiple Choice")
        self.assertEqual(len(self.lib_page.xblocks), 10)
        add_component(self.lib_page, "problem", "Multiple Choice")
        self.assertEqual(len(self.lib_page.xblocks), 1)
        self.lib_page.click_delete_button(self.lib_page.xblocks[0].locator)
        self.assertEqual(len(self.lib_page.xblocks), 10)

    @data('top', 'bottom')
    def test_nav_present_but_disabled(self, position):
        """
        Scenario: Ensure that the navigation buttons aren't active when there aren't enough XBlocks.
        Given that I have a library in Studio with no XBlocks
        The Navigation buttons should be disabled.
        When I add a multiple choice problem
        The Navigation buttons should be disabled.
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        self.assertTrue(self.lib_page.nav_disabled(position))
        add_component(self.lib_page, "problem", "Multiple Choice")
        self.assertTrue(self.lib_page.nav_disabled(position))

    def test_delete_deletes_only_desired_block(self):
        """
        Scenario: Ensure that when deleting XBlock only desired XBlock is deleted
        Given that I have a library in Studio with no XBlocks
        And I create Blank Common Problem XBlock
        And I create Checkboxes XBlock
        When I delete Blank Problem XBlock
        Then Checkboxes XBlock is not deleted
        And Blank Common Problem XBlock is deleted
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        add_component(self.lib_page, "problem", "Blank Common Problem")
        add_component(self.lib_page, "problem", "Checkboxes")
        self.assertEqual(len(self.lib_page.xblocks), 2)
        self.assertIn("Blank Common Problem", self.lib_page.xblocks[0].name)
        self.assertIn("Checkboxes", self.lib_page.xblocks[1].name)
        self.lib_page.click_delete_button(self.lib_page.xblocks[0].locator)
        self.assertEqual(len(self.lib_page.xblocks), 1)
        problem_block = self.lib_page.xblocks[0]
        self.assertIn("Checkboxes", problem_block.name)


@attr(shard=2)
@ddt
class LibraryNavigationTest(StudioLibraryTest):
    """
    Test common Navigation actions
    """
    def setUp(self):
        """
        Ensure a library exists and navigate to the library edit page.
        """
        super(LibraryNavigationTest, self).setUp()
        self.lib_page = LibraryEditPage(self.browser, self.library_key)
        self.lib_page.visit()
        self.lib_page.wait_until_ready()

    def populate_library_fixture(self, library_fixture):
        """
        Create four pages worth of XBlocks, and offset by one so each is named
        after the number they should be in line by the user's perception.
        """
        self.blocks = [XBlockFixtureDesc('html', str(i)) for i in xrange(1, 41)]
        library_fixture.add_children(*self.blocks)

    def test_arbitrary_page_selection(self):
        """
        Scenario: I can pick a specific page number of a Library at will.
        Given that I have a library in Studio with 40 XBlocks
        When I go to the 3rd page
        The first XBlock should be the 21st XBlock
        When I go to the 4th Page
        The first XBlock should be the 31st XBlock
        When I go to the 1st page
        The first XBlock should be the 1st XBlock
        When I go to the 2nd page
        The first XBlock should be the 11th XBlock
        """
        self.lib_page.go_to_page(3)
        self.assertEqual(self.lib_page.xblocks[0].name, '21')
        self.lib_page.go_to_page(4)
        self.assertEqual(self.lib_page.xblocks[0].name, '31')
        self.lib_page.go_to_page(1)
        self.assertEqual(self.lib_page.xblocks[0].name, '1')
        self.lib_page.go_to_page(2)
        self.assertEqual(self.lib_page.xblocks[0].name, '11')

    def test_bogus_page_selection(self):
        """
        Scenario: I can't pick a nonsense page number of a Library
        Given that I have a library in Studio with 40 XBlocks
        When I attempt to go to the 'a'th page
        The input field will be cleared and no change of XBlocks will be made
        When I attempt to visit the 5th page
        The input field will be cleared and no change of XBlocks will be made
        When I attempt to visit the -1st page
        The input field will be cleared and no change of XBlocks will be made
        When I attempt to visit the 0th page
        The input field will be cleared and no change of XBlocks will be made
        """
        self.assertEqual(self.lib_page.xblocks[0].name, '1')
        self.lib_page.go_to_page('a')
        self.assertTrue(self.lib_page.check_page_unchanged('1'))
        self.lib_page.go_to_page(-1)
        self.assertTrue(self.lib_page.check_page_unchanged('1'))
        self.lib_page.go_to_page(5)
        self.assertTrue(self.lib_page.check_page_unchanged('1'))
        self.lib_page.go_to_page(0)
        self.assertTrue(self.lib_page.check_page_unchanged('1'))

    @data('top', 'bottom')
    def test_nav_buttons(self, position):
        """
        Scenario: Ensure that the navigation buttons work.
        Given that I have a library in Studio with 40 XBlocks
        The previous button should be disabled.
        The first XBlock should be the 1st XBlock
        Then if I hit the next button
        The first XBlock should be the 11th XBlock
        Then if I hit the next button
        The first XBlock should be the 21st XBlock
        Then if I hit the next button
        The first XBlock should be the 31st XBlock
        And the next button should be disabled
        Then if I hit the previous button
        The first XBlock should be the 21st XBlock
        Then if I hit the previous button
        The first XBlock should be the 11th XBlock
        Then if I hit the previous button
        The first XBlock should be the 1st XBlock
        And the previous button should be disabled
        """
        # Check forward navigation
        self.assertTrue(self.lib_page.nav_disabled(position, ['previous']))
        self.assertEqual(self.lib_page.xblocks[0].name, '1')
        self.lib_page.move_forward(position)
        self.assertEqual(self.lib_page.xblocks[0].name, '11')
        self.lib_page.move_forward(position)
        self.assertEqual(self.lib_page.xblocks[0].name, '21')
        self.lib_page.move_forward(position)
        self.assertEqual(self.lib_page.xblocks[0].name, '31')
        self.lib_page.nav_disabled(position, ['next'])

        # Check backward navigation
        self.lib_page.move_back(position)
        self.assertEqual(self.lib_page.xblocks[0].name, '21')
        self.lib_page.move_back(position)
        self.assertEqual(self.lib_page.xblocks[0].name, '11')
        self.lib_page.move_back(position)
        self.assertEqual(self.lib_page.xblocks[0].name, '1')
        self.assertTrue(self.lib_page.nav_disabled(position, ['previous']))

    def test_library_pagination(self):
        """
        Scenario: Ensure that adding several XBlocks to a library results in pagination.
        Given that I have a library in Studio with 40 XBlocks
        Then 10 are displayed
        And the first XBlock will be the 1st one
        And I'm on the 1st page
        When I add 1 Multiple Choice XBlock
        Then 1 XBlock will be displayed
        And I'm on the 5th page
        The first XBlock will be the newest one
        When I delete that XBlock
        Then 10 are displayed
        And I'm on the 4th page
        And the first XBlock is the 31st one
        And the last XBlock is the 40th one.
        """
        self.assertEqual(len(self.lib_page.xblocks), 10)
        self.assertEqual(self.lib_page.get_page_number(), '1')
        self.assertEqual(self.lib_page.xblocks[0].name, '1')
        add_component(self.lib_page, "problem", "Multiple Choice")
        self.assertEqual(len(self.lib_page.xblocks), 1)
        self.assertEqual(self.lib_page.get_page_number(), '5')
        self.assertEqual(self.lib_page.xblocks[0].name, "Multiple Choice")
        self.lib_page.click_delete_button(self.lib_page.xblocks[0].locator)
        self.assertEqual(len(self.lib_page.xblocks), 10)
        self.assertEqual(self.lib_page.get_page_number(), '4')
        self.assertEqual(self.lib_page.xblocks[0].name, '31')
        self.assertEqual(self.lib_page.xblocks[-1].name, '40')

    def test_delete_shifts_blocks(self):
        """
        Scenario: Ensure that removing an XBlock shifts other blocks back.
        Given that I have a library in Studio with 40 XBlocks
        Then 10 are displayed
        And I will be on the first page
        When I delete the third XBlock
        There will be 10 displayed
        And the first XBlock will be the first one
        And the last XBlock will be the 11th one
        And I will be on the first page
        """
        self.assertEqual(len(self.lib_page.xblocks), 10)
        self.assertEqual(self.lib_page.get_page_number(), '1')
        self.lib_page.click_delete_button(self.lib_page.xblocks[2].locator, confirm=True)
        self.assertEqual(len(self.lib_page.xblocks), 10)
        self.assertEqual(self.lib_page.xblocks[0].name, '1')
        self.assertEqual(self.lib_page.xblocks[-1].name, '11')
        self.assertEqual(self.lib_page.get_page_number(), '1')

    def test_previews(self):
        """
        Scenario: Ensure the user is able to hide previews of XBlocks.
        Given that I have a library in Studio with 40 XBlocks
        Then previews are visible
        And when I click the toggle previews button
        Then the previews will not be visible
        And when I click the toggle previews button
        Then the previews are visible
        """
        self.assertTrue(self.lib_page.are_previews_showing())
        self.lib_page.toggle_previews()
        self.assertFalse(self.lib_page.are_previews_showing())
        self.lib_page.toggle_previews()
        self.assertTrue(self.lib_page.are_previews_showing())

    def test_previews_navigation(self):
        """
        Scenario: Ensure preview settings persist across navigation.
        Given that I have a library in Studio with 40 XBlocks
        Then previews are visible
        And when I click the toggle previews button
        And click the next page button
        Then the previews will not be visible
        And the first XBlock will be the 11th one
        And the last XBlock will be the 20th one
        And when I click the toggle previews button
        And I click the previous page button
        Then the previews will be visible
        And the first XBlock will be the first one
        And the last XBlock will be the 11th one
        """
        self.assertTrue(self.lib_page.are_previews_showing())
        self.lib_page.toggle_previews()
        # Which set of arrows shouldn't matter for this test.
        self.lib_page.move_forward('top')
        self.assertFalse(self.lib_page.are_previews_showing())
        self.assertEqual(self.lib_page.xblocks[0].name, '11')
        self.assertEqual(self.lib_page.xblocks[-1].name, '20')
        self.lib_page.toggle_previews()
        self.lib_page.move_back('top')
        self.assertTrue(self.lib_page.are_previews_showing())
        self.assertEqual(self.lib_page.xblocks[0].name, '1')
        self.assertEqual(self.lib_page.xblocks[-1].name, '10')

    def test_preview_state_persistance(self):
        """
        Scenario: Ensure preview state persists between page loads.
        Given that I have a library in Studio with 40 XBlocks
        Then previews are visible
        And when I click the toggle previews button
        And I revisit the page
        Then the previews will not be visible
        """
        self.assertTrue(self.lib_page.are_previews_showing())
        self.lib_page.toggle_previews()
        self.lib_page.visit()
        self.lib_page.wait_until_ready()
        self.assertFalse(self.lib_page.are_previews_showing())

    def test_preview_add_xblock(self):
        """
        Scenario: Ensure previews are shown when adding new blocks, regardless of preview setting.
        Given that I have a library in Studio with 40 XBlocks
        Then previews are visible
        And when I click the toggle previews button
        Then the previews will not be visible
        And when I add an XBlock
        Then I will be on the 5th page
        And the XBlock will have loaded a preview
        And when I revisit the library
        And I go to the 5th page
        Then the top XBlock will be the one I added
        And it will not have a preview
        And when I add an XBlock
        Then the XBlock I added will have a preview
        And the top XBlock will not have one.
        """
        self.assertTrue(self.lib_page.are_previews_showing())
        self.lib_page.toggle_previews()
        self.assertFalse(self.lib_page.are_previews_showing())
        add_component(self.lib_page, "problem", "Checkboxes")
        self.assertEqual(self.lib_page.get_page_number(), '5')
        first_added = self.lib_page.xblocks[0]
        self.assertIn("Checkboxes", first_added.name)
        self.assertFalse(self.lib_page.xblocks[0].is_placeholder())
        self.lib_page.visit()
        self.lib_page.wait_until_ready()
        self.lib_page.go_to_page(5)
        self.assertTrue(self.lib_page.xblocks[0].is_placeholder())
        add_component(self.lib_page, "problem", "Multiple Choice")
        # DOM has detatched the element since last assignment
        first_added = self.lib_page.xblocks[0]
        second_added = self.lib_page.xblocks[1]
        self.assertIn("Multiple Choice", second_added.name)
        self.assertFalse(second_added.is_placeholder())
        self.assertTrue(first_added.is_placeholder())

    def test_edit_with_preview(self):
        """
        Scenario: Editing an XBlock should show me a preview even if previews are hidden.
        Given that I have a library in Studio with 40 XBlocks
        Then previews are visible
        And when I click the toggle previews button
        Then the previews will not be visible
        And when I edit the first XBlock
        Then the first XBlock will show a preview
        And the other XBlocks will still be placeholders
        """
        self.assertTrue(self.lib_page.are_previews_showing())
        self.lib_page.toggle_previews()
        self.assertFalse(self.lib_page.are_previews_showing())
        target = self.lib_page.xblocks[0]
        target.edit()
        target.save_settings()
        self.assertFalse(target.is_placeholder())
        self.assertTrue(all([xblock.is_placeholder() for xblock in self.lib_page.xblocks[1:]]))

    def test_duplicate_xblock_pagination(self):
        """
        Scenario: Duplicating an XBlock should not shift the page if the XBlock is not at the end.
        Given that I have a library in Studio with 40 XBlocks
        When I duplicate the third XBlock
        Then the page should not change
        And the duplicate XBlock should be there
        And it should show a preview
        And there should not be more than 10 XBlocks visible.
        """
        third_block_id = self.lib_page.xblocks[2].locator
        self.lib_page.click_duplicate_button(third_block_id)
        self.lib_page.wait_until_ready()
        target = self.lib_page.xblocks[3]
        self.assertIn('Duplicate', target.name)
        self.assertFalse(target.is_placeholder())
        self.assertEqual(len(self.lib_page.xblocks), 10)

    def test_duplicate_xblock_pagination_end(self):
        """
        Scenario: Duplicating an XBlock if it's the last one should bring me to the next page with a preview.
        Given that I have a library in Studio with 40 XBlocks
        And when I hide previews
        And I duplicate the last XBlock
        The page should change to page 2
        And the duplicate XBlock should be the first XBlock
        And it should not be a placeholder
        """
        self.lib_page.toggle_previews()
        last_block_id = self.lib_page.xblocks[-1].locator
        self.lib_page.click_duplicate_button(last_block_id)
        self.lib_page.wait_until_ready()
        self.assertEqual(self.lib_page.get_page_number(), '2')
        target_block = self.lib_page.xblocks[0]
        self.assertIn('Duplicate', target_block.name)
        self.assertFalse(target_block.is_placeholder())


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
            ],
        })

        lib_page.a11y_audit.check_for_accessibility_errors()
