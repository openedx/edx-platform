"""
Acceptance tests for Library Content in LMS
"""
import textwrap
import ddt
from unittest import skip

from .base_studio_test import StudioLibraryTest
from ...fixtures.course import CourseFixture
from ..helpers import UniqueCourseTest
from ...pages.studio.library import StudioLibraryContentXBlockEditModal, StudioLibraryContainerXBlockWrapper
from ...pages.studio.overview import CourseOutlinePage
from ...fixtures.course import XBlockFixtureDesc

SECTION_NAME = 'Test Section'
SUBSECTION_NAME = 'Test Subsection'
UNIT_NAME = 'Test Unit'


@ddt.ddt
class StudioLibraryContainerTest(StudioLibraryTest, UniqueCourseTest):
    """
    Test Library Content block in LMS
    """
    def setUp(self):
        """
        Install library with some content and a course using fixtures
        """
        super(StudioLibraryContainerTest, self).setUp()
        # Also create a course:
        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )
        self.populate_course_fixture(self.course_fixture)
        self.course_fixture.install()
        self.outline = CourseOutlinePage(
            self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run']
        )

        self.outline.visit()
        subsection = self.outline.section(SECTION_NAME).subsection(SUBSECTION_NAME)
        self.unit_page = subsection.toggle_expand().unit(UNIT_NAME).go_to()

    def populate_library_fixture(self, library_fixture):
        """
        Populate the children of the test course fixture.
        """
        library_fixture.add_children(
            XBlockFixtureDesc("html", "Html1"),
            XBlockFixtureDesc("html", "Html2"),
            XBlockFixtureDesc("html", "Html3"),
        )

    def populate_course_fixture(self, course_fixture):
        """ Install a course with sections/problems, tabs, updates, and handouts """
        library_content_metadata = {
            'source_libraries': [self.library_key],
            'mode': 'random',
            'max_count': 1,
            'has_score': False
        }

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', SECTION_NAME).add_children(
                XBlockFixtureDesc('sequential', SUBSECTION_NAME).add_children(
                    XBlockFixtureDesc('vertical', UNIT_NAME).add_children(
                        XBlockFixtureDesc('library_content', "Library Content", metadata=library_content_metadata)
                    )
                )
            )
        )

    def _get_library_xblock_wrapper(self, xblock):
        """
        Wraps xblock into :class:`...pages.studio.library.StudioLibraryContainerXBlockWrapper`
        """
        return StudioLibraryContainerXBlockWrapper.from_xblock_wrapper(xblock)

    @ddt.data(
        ('library-v1:111+111', 1, True),
        ('library-v1:edX+L104', 2, False),
        ('library-v1:OtherX+IDDQD', 3, True),
    )
    @ddt.unpack
    def test_can_edit_metadata(self, library_key, max_count, scored):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And I edit library content metadata and save it
        Then I can ensure that data is persisted
        """
        library_container = self._get_library_xblock_wrapper(self.unit_page.xblocks[0])
        edit_modal = StudioLibraryContentXBlockEditModal(library_container.edit())
        edit_modal.library_key = library_key
        edit_modal.count = max_count
        edit_modal.scored = scored

        library_container.save_settings()  # saving settings

        # open edit window again to verify changes are persistent
        edit_modal = StudioLibraryContentXBlockEditModal(library_container.edit())
        self.assertEqual(edit_modal.library_key, library_key)
        self.assertEqual(edit_modal.count, max_count)
        self.assertEqual(edit_modal.scored, scored)

    def test_no_library_shows_library_not_configured(self):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And I edit set library key to none
        Then I can see that library content block is misconfigured
        """
        expected_text = 'A library has not yet been selected.'
        expected_action = 'Select a Library'
        library_container = self._get_library_xblock_wrapper(self.unit_page.xblocks[0])

        # precondition check - the library block should be configured before we remove the library setting
        self.assertFalse(library_container.has_validation_not_configured_warning)

        edit_modal = StudioLibraryContentXBlockEditModal(library_container.edit())
        edit_modal.library_key = None
        library_container.save_settings()

        self.assertTrue(library_container.has_validation_not_configured_warning)
        self.assertIn(expected_text, library_container.validation_not_configured_warning_text)
        self.assertIn(expected_action, library_container.validation_not_configured_warning_text)

    def test_set_missing_library_shows_correct_label(self):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And I edit set library key to non-existent library
        Then I can see that library content block is misconfigured
        """
        nonexistent_lib_key = 'library-v1:111+111'
        expected_text = "Library is invalid, corrupt, or has been deleted."

        library_container = self._get_library_xblock_wrapper(self.unit_page.xblocks[0])

        # precondition check - assert library is configured before we remove it
        self.assertFalse(library_container.has_validation_error)

        edit_modal = StudioLibraryContentXBlockEditModal(library_container.edit())
        edit_modal.library_key = nonexistent_lib_key

        library_container.save_settings()

        self.assertTrue(library_container.has_validation_error)
        self.assertIn(expected_text, library_container.validation_error_text)

    def test_out_of_date_message(self):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        Then I update the library being used
        Then I refresh the page
        Then I can see that library content block needs to be updated
        When I click on the update link
        Then I can see that the content no longer needs to be updated
        """
        expected_text = "This component is out of date. The library has new content."
        library_block = self._get_library_xblock_wrapper(self.unit_page.xblocks[0])

        self.assertFalse(library_block.has_validation_warning)
        # Removed this assert until a summary message is added back to the author view (SOL-192)
        #self.assertIn("3 matching components", library_block.author_content)

        self.library_fixture.create_xblock(self.library_fixture.library_location, XBlockFixtureDesc("html", "Html4"))

        self.unit_page.visit()  # Reload the page

        self.assertTrue(library_block.has_validation_warning)
        self.assertIn(expected_text, library_block.validation_warning_text)

        library_block.refresh_children()

        self.unit_page.wait_for_page()  # Wait for the page to reload
        library_block = self._get_library_xblock_wrapper(self.unit_page.xblocks[0])

        self.assertFalse(library_block.has_validation_message)
        # Removed this assert until a summary message is added back to the author view (SOL-192)
        #self.assertIn("4 matching components", library_block.author_content)

    def test_no_content_message(self):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And I set Problem Type selector so that no libraries have matching content
        Then I can see that "No matching content" warning is shown
        When I set Problem Type selector so that there is matching content
        Then I can see that warning messages are not shown
        """
        # Add a single "Dropdown" type problem to the library (which otherwise has only HTML blocks):
        self.library_fixture.create_xblock(self.library_fixture.library_location, XBlockFixtureDesc(
            "problem", "Dropdown",
            data=textwrap.dedent("""
                <problem>
                    <p>Dropdown</p>
                    <optionresponse><optioninput label="Dropdown" options="('1', '2')" correct="'2'"></optioninput></optionresponse>
                </problem>
                """)
        ))

        expected_text = 'There are no matching problem types in the specified libraries. Select another problem type'

        library_container = self._get_library_xblock_wrapper(self.unit_page.xblocks[0])

        # precondition check - assert library has children matching filter criteria
        self.assertFalse(library_container.has_validation_error)
        self.assertFalse(library_container.has_validation_warning)

        edit_modal = StudioLibraryContentXBlockEditModal(library_container.edit())
        self.assertEqual(edit_modal.capa_type, "Any Type")  # precondition check
        edit_modal.capa_type = "Custom Evaluated Script"

        library_container.save_settings()

        self.assertTrue(library_container.has_validation_warning)
        self.assertIn(expected_text, library_container.validation_warning_text)

        edit_modal = StudioLibraryContentXBlockEditModal(library_container.edit())
        self.assertEqual(edit_modal.capa_type, "Custom Evaluated Script")  # precondition check
        edit_modal.capa_type = "Dropdown"
        library_container.save_settings()

        # Library should contain single Dropdown problem, so now there should be no errors again
        self.assertFalse(library_container.has_validation_error)
        self.assertFalse(library_container.has_validation_warning)

    def test_not_enough_children_blocks(self):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And I set Problem Type selector so "Any"
        Then I can see that "No matching content" warning is shown
        """
        expected_tpl = "The specified libraries are configured to fetch {count} problems, " \
                       "but there are only {actual} matching problems."

        library_container = self._get_library_xblock_wrapper(self.unit_page.xblocks[0])

        # precondition check - assert block is configured fine
        self.assertFalse(library_container.has_validation_error)
        self.assertFalse(library_container.has_validation_warning)

        edit_modal = StudioLibraryContentXBlockEditModal(library_container.edit())
        edit_modal.count = 50
        library_container.save_settings()

        self.assertTrue(library_container.has_validation_warning)
        self.assertIn(
            expected_tpl.format(count=50, actual=len(self.library_fixture.children)),
            library_container.validation_warning_text
        )

    @skip("Flaky: 01/16/2015")
    def test_settings_overrides(self):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And when I click the "View" link
        Then I can see a preview of the blocks drawn from the library.

        When I edit one of the blocks to change a setting such as "display_name",
        Then I can see the new setting is overriding the library version.

        When I subsequently click to refresh the content with the latest from the library,
        Then I can see that the overrided version of the setting is preserved.

        When I click to edit the block and reset the setting,
        then I can see that the setting's field defaults back to the library version.
        """
        block_wrapper_unit_page = self._get_library_xblock_wrapper(self.unit_page.xblocks[0].children[0])
        container_page = block_wrapper_unit_page.go_to_container()
        library_block = self._get_library_xblock_wrapper(container_page.xblocks[0])

        self.assertFalse(library_block.has_validation_message)
        self.assertEqual(len(library_block.children), 3)

        block = library_block.children[0]
        self.assertIn(block.name, ("Html1", "Html2", "Html3"))
        name_default = block.name

        block.edit()
        new_display_name = "A new name for this HTML block"
        block.set_field_val("Display Name", new_display_name)
        block.save_settings()

        self.assertEqual(block.name, new_display_name)

        # Create a new block, causing a new library version:
        self.library_fixture.create_xblock(self.library_fixture.library_location, XBlockFixtureDesc("html", "Html4"))

        container_page.visit()  # Reload
        self.assertTrue(library_block.has_validation_warning)
        library_block.refresh_children()
        container_page.wait_for_page()  # Wait for the page to reload

        self.assertEqual(len(library_block.children), 4)
        self.assertEqual(block.name, new_display_name)

        # Reset:
        block.edit()
        block.reset_field_val("Display Name")
        block.save_settings()
        self.assertEqual(block.name, name_default)
