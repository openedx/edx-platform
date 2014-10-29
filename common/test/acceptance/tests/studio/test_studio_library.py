"""
Acceptance tests for Content Libraries in Studio
"""

from .base_studio_test import StudioLibraryTest
from ...pages.studio.utils import add_component
from ...pages.studio.library import LibraryPage


class LibraryEditPageTest(StudioLibraryTest):
    """
    Test the functionality of the library edit page.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        """
        Ensure a library exists and navigate to the library edit page.
        """
        super(LibraryEditPageTest, self).setUp(is_staff=True)
        self.lib_page = LibraryPage(self.browser, self.library_key)
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
        self.assertIn("Laura Roslin", problem_block.student_content)
