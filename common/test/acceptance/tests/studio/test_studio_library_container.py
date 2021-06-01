"""
Acceptance tests for Library Content in LMS
"""


import textwrap

import ddt
import six

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.studio.library import StudioLibraryContainerXBlockWrapper, StudioLibraryContentEditor
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.tests.helpers import TestWithSearchIndexMixin, UniqueCourseTest
from common.test.acceptance.tests.studio.base_studio_test import StudioLibraryTest

SECTION_NAME = 'Test Section'
SUBSECTION_NAME = 'Test Subsection'
UNIT_NAME = 'Test Unit'


@ddt.ddt
class StudioLibraryContainerTest(StudioLibraryTest, UniqueCourseTest, TestWithSearchIndexMixin):
    """
    Test Library Content block in LMS
    """
    shard = 17

    def setUp(self):
        """
        Install library with some content and a course using fixtures
        """
        self._create_search_index()
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
        self.unit_page = subsection.expand_subsection().unit(UNIT_NAME).go_to()

    def tearDown(self):
        """ Tear down method: remove search index backing file """
        self._cleanup_index_file()
        super(StudioLibraryContainerTest, self).tearDown()

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
            'source_library_id': six.text_type(self.library_key),
            'mode': 'random',
            'max_count': 1,
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

    @ddt.data(1, 2, 3)
    def test_can_edit_metadata(self, max_count):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And I edit library content metadata and save it
        Then I can ensure that data is persisted
        """
        library_name = self.library_info['display_name']
        library_container = self._get_library_xblock_wrapper(self.unit_page.xblocks[1])
        library_container.edit()
        edit_modal = StudioLibraryContentEditor(self.browser, library_container.locator)
        edit_modal.library_name = library_name
        edit_modal.count = max_count

        library_container.save_settings()  # saving settings

        # open edit window again to verify changes are persistent
        library_container.edit()
        edit_modal = StudioLibraryContentEditor(self.browser, library_container.locator)
        self.assertEqual(edit_modal.library_name, library_name)
        self.assertEqual(edit_modal.count, max_count)

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

        library_container = self._get_library_xblock_wrapper(self.unit_page.xblocks[1])

        # precondition check - assert library has children matching filter criteria
        self.assertFalse(library_container.has_validation_error)
        self.assertFalse(library_container.has_validation_warning)

        library_container.edit()
        edit_modal = StudioLibraryContentEditor(self.browser, library_container.locator)
        self.assertEqual(edit_modal.capa_type, "Any Type")  # precondition check
        edit_modal.capa_type = "Custom Evaluated Script"

        library_container.save_settings()

        self.assertTrue(library_container.has_validation_warning)
        self.assertIn(expected_text, library_container.validation_warning_text)

        library_container.edit()
        edit_modal = StudioLibraryContentEditor(self.browser, library_container.locator)
        self.assertEqual(edit_modal.capa_type, "Custom Evaluated Script")  # precondition check
        edit_modal.capa_type = "Dropdown"
        library_container.save_settings()

        # Library should contain single Dropdown problem, so now there should be no errors again
        self.assertFalse(library_container.has_validation_error)
        self.assertFalse(library_container.has_validation_warning)

    def test_cannot_manage(self):
        """
        Scenario: Given I have a library, a course and library content xblock in a course
        When I go to studio unit page for library content block
        And when I click the "View" link
        Then I can see a preview of the blocks drawn from the library.

        And I do not see a duplicate button
        And I do not see a delete button
        """
        block_wrapper_unit_page = self._get_library_xblock_wrapper(self.unit_page.xblocks[0].children[0])
        container_page = block_wrapper_unit_page.go_to_container()

        for block in container_page.xblocks:
            self.assertFalse(block.has_duplicate_button)
            self.assertFalse(block.has_delete_button)
            self.assertFalse(block.has_edit_visibility_button)
