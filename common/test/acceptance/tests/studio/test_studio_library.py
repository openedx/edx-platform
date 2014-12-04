"""
Acceptance tests for Content Libraries in Studio
"""
from ddt import ddt, data

from .base_studio_test import StudioLibraryTest
from ...pages.studio.utils import add_component
from ...pages.studio.library import LibraryPage


@ddt
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
        for _ in range(0, 10):
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
        When I add 5 multiple Choice XBlocks
        The Navigation buttons should be disabled.
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        self.assertTrue(self.lib_page.nav_disabled(position))
        for _ in range(0, 5):
            add_component(self.lib_page, "problem", "Multiple Choice")
        self.assertTrue(self.lib_page.nav_disabled(position))

    @data('top', 'bottom')
    def test_nav_buttons(self, position):
        """
        Scenario: Ensure that the navigation buttons work.
        Given that I have a library in Studio with no XBlocks
        And I create 10 Multiple Choice XBlocks
        And I create 10 Checkbox XBlocks
        And I create 10 Dropdown XBlocks
        And I revisit the page
        The previous button should be disabled.
        The first XBlock should be a Multiple Choice XBlock
        Then if I hit the next button
        The first XBlock should be a Checkboxes XBlock
        Then if I hit the next button
        The first XBlock should be a Dropdown XBlock
        And the next button should be disabled
        Then if I hit the previous button
        The first XBlock should be an Checkboxes XBlock
        Then if I hit the previous button
        The first XBlock should be a Multipe Choice XBlock
        And the previous button should be disabled
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        block_types = [('problem', 'Multiple Choice'), ('problem', 'Checkboxes'), ('problem', 'Dropdown')]
        for block_type in block_types:
            for _ in range(0, 10):
                add_component(self.lib_page, *block_type)

        # Don't refresh, as that may contain additional state.
        self.lib_page.revisit()

        # Check forward navigation
        self.assertTrue(self.lib_page.nav_disabled(position, ['previous']))
        self.assertEqual(self.lib_page.xblocks[0].name, 'Multiple Choice')
        self.lib_page.move_forward(position)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Checkboxes')
        self.lib_page.move_forward(position)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Dropdown')
        self.lib_page.nav_disabled(position, ['next'])

        # Check backward navigation
        self.lib_page.move_back(position)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Checkboxes')
        self.lib_page.move_back(position)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Multiple Choice')
        self.assertTrue(self.lib_page.nav_disabled(position, ['previous']))

    def test_arbitrary_page_selection(self):
        """
        Scenario: I can pick a specific page number of a Library at will.
        Given that I have a library in Studio with no XBlocks
        And I create 10 Multiple Choice XBlocks
        And I create 10 Checkboxes XBlocks
        And I create 10 Dropdown XBlocks
        And I create 10 Numerical Input XBlocks
        And I revisit the page
        When I go to the 3rd page
        The first XBlock should be a Dropdown XBlock
        When I go to the 4th Page
        The first XBlock should be a Numerical Input XBlock
        When I go to the 1st page
        The first XBlock should be a Multiple Choice XBlock
        When I go to the 2nd page
        The first XBlock should be a Checkboxes XBlock
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        block_types = [
            ('problem', 'Multiple Choice'), ('problem', 'Checkboxes'), ('problem', 'Dropdown'),
            ('problem', 'Numerical Input'),
        ]
        for block_type in block_types:
            for _ in range(0, 10):
                add_component(self.lib_page, *block_type)

        # Don't refresh, as that may contain additional state.
        self.lib_page.revisit()
        self.lib_page.go_to_page(3)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Dropdown')
        self.lib_page.go_to_page(4)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Numerical Input')
        self.lib_page.go_to_page(1)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Multiple Choice')
        self.lib_page.go_to_page(2)
        self.assertEqual(self.lib_page.xblocks[0].name, 'Checkboxes')

    def test_bogus_page_selection(self):
        """
        Scenario: I can't pick a nonsense page number of a Library
        Given that I have a library in Studio with no XBlocks
        And I create 10 Multiple Choice XBlocks
        And I create 10 Checkboxes XBlocks
        And I create 10 Dropdown XBlocks
        And I create 10 Numerical Input XBlocks
        And I revisit the page
        When I attempt to go to the 'a'th page
        The input field will be cleared and no change of XBlocks will be made
        When I attempt to visit the 5th page
        The input field will be cleared and no change of XBlocks will be made
        When I attempt to visit the -1st page
        The input field will be cleared and no change of XBlocks will be made
        When I attempt to visit the 0th page
        The input field will be cleared and no change of XBlocks will be made
        """
        self.assertEqual(len(self.lib_page.xblocks), 0)
        block_types = [
            ('problem', 'Multiple Choice'), ('problem', 'Checkboxes'), ('problem', 'Dropdown'),
            ('problem', 'Numerical Input'),
        ]
        for block_type in block_types:
            for _ in range(0, 10):
                add_component(self.lib_page, *block_type)

        self.lib_page.revisit()
        self.assertEqual(self.lib_page.xblocks[0].name, 'Multiple Choice')
        self.lib_page.go_to_page('a')
        self.assertTrue(self.lib_page.check_page_unchanged('Multiple Choice'))
        self.lib_page.go_to_page(-1)
        self.assertTrue(self.lib_page.check_page_unchanged('Multiple Choice'))
        self.lib_page.go_to_page(5)
        self.assertTrue(self.lib_page.check_page_unchanged('Multiple Choice'))
        self.lib_page.go_to_page(0)
        self.assertTrue(self.lib_page.check_page_unchanged('Multiple Choice'))
