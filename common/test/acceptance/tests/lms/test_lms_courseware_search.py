"""
Test courseware search
"""
import json

from flaky import flaky
from nose.plugins.attrib import attr

from common.test.acceptance.tests.helpers import UniqueCourseTest, remove_file
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.common.utils import click_css
from common.test.acceptance.pages.studio.utils import add_html_component, type_in_codemirror
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage as StudioCourseOutlinePage
from common.test.acceptance.pages.studio.container import ContainerPage
from common.test.acceptance.pages.lms.courseware_search import CoursewareSearchPage
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc


@attr(shard=5)
class CoursewareSearchTest(UniqueCourseTest):
    """
    Test courseware search.
    """
    USERNAME = 'STUDENT_TESTER'
    EMAIL = 'student101@example.com'

    STAFF_USERNAME = "STAFF_TESTER"
    STAFF_EMAIL = "staff101@example.com"

    HTML_CONTENT = """
            Someday I'll wish upon a star
            And wake up where the clouds are far
            Behind me.
            Where troubles melt like lemon drops
            Away above the chimney tops
            That's where you'll find me.
        """
    SEARCH_STRING = "chimney"
    EDITED_CHAPTER_NAME = "Section 2 - edited"
    EDITED_SEARCH_STRING = "edited"

    TEST_INDEX_FILENAME = "test_root/index_file.dat"

    def setUp(self):
        """
        Create search page and course content to search
        """
        # create test file in which index for this test will live
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)
        self.addCleanup(remove_file, self.TEST_INDEX_FILENAME)

        super(CoursewareSearchTest, self).setUp()
        self.courseware_search_page = CoursewareSearchPage(self.browser, self.course_id)

        self.studio_course_outline = StudioCourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Subsection 1')
            )
        ).add_children(
            XBlockFixtureDesc('chapter', 'Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Subsection 2')
            )
        ).install()

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, username=username, email=email,
                     course_id=self.course_id, staff=staff).visit()

    def _studio_publish_content(self, section_index):
        """
        Publish content on studio course page under specified section
        """
        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)
        self.studio_course_outline.visit()
        subsection = self.studio_course_outline.section_at(section_index).subsection_at(0)
        subsection.expand_subsection()
        unit = subsection.unit_at(0)
        unit.publish()

    def _studio_edit_chapter_name(self, section_index):
        """
        Edit chapter name on studio course page under specified section
        """
        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)
        self.studio_course_outline.visit()
        section = self.studio_course_outline.section_at(section_index)
        section.change_name(self.EDITED_CHAPTER_NAME)

    def _studio_add_content(self, section_index):
        """
        Add content on studio course page under specified section
        """

        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)
        # create a unit in course outline
        self.studio_course_outline.visit()
        subsection = self.studio_course_outline.section_at(section_index).subsection_at(0)
        subsection.expand_subsection()
        subsection.add_unit()

        # got to unit and create an HTML component and save (not publish)
        unit_page = ContainerPage(self.browser, None)
        unit_page.wait_for_page()
        add_html_component(unit_page, 0)
        unit_page.wait_for_element_presence('.edit-button', 'Edit button is visible')
        click_css(unit_page, '.edit-button', 0, require_notification=False)
        unit_page.wait_for_element_visibility('.modal-editor', 'Modal editor is visible')
        type_in_codemirror(unit_page, 0, self.HTML_CONTENT)
        click_css(unit_page, '.action-save', 0)

    def _studio_reindex(self):
        """
        Reindex course content on studio course page
        """

        self._auto_auth(self.STAFF_USERNAME, self.STAFF_EMAIL, True)
        self.studio_course_outline.visit()
        self.studio_course_outline.start_reindex()
        self.studio_course_outline.wait_for_ajax()

    def _search_for_content(self, search_term):
        """
        Login and search for specific content

        Arguments:
            search_term - term to be searched for

        Returns:
            (bool) True if search term is found in resulting content; False if not found
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()
        self.courseware_search_page.search_for_term(search_term)
        return search_term in self.courseware_search_page.search_results.html[0]

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()

    def test_search(self):
        """
        Make sure that you can search for something.
        """

        # Create content in studio without publishing.
        self._studio_add_content(0)

        # Do a search, there should be no results shown.
        self.assertFalse(self._search_for_content(self.SEARCH_STRING))

        # Publish in studio to trigger indexing.
        self._studio_publish_content(0)

        # Do the search again, this time we expect results.
        self.assertTrue(self._search_for_content(self.SEARCH_STRING))

    @flaky  # TNL-5771
    def test_reindex(self):
        """
        Make sure new content gets reindexed on button press.
        """

        # Create content in studio without publishing.
        self._studio_add_content(1)

        # Do a search, there should be no results shown.
        self.assertFalse(self._search_for_content(self.EDITED_SEARCH_STRING))

        # Publish in studio to trigger indexing, and edit chapter name afterwards.
        self._studio_publish_content(1)

        # Do a ReIndex from studio to ensure that our stuff is updated before the next stage of the test
        self._studio_reindex()

        # Search after publish, there should still be no results shown.
        self.assertFalse(self._search_for_content(self.EDITED_SEARCH_STRING))

        self._studio_edit_chapter_name(1)

        # Do a ReIndex from studio to ensure that our stuff is updated before the next stage of the test
        self._studio_reindex()

        # Do the search again, this time we expect results.
        self.assertTrue(self._search_for_content(self.EDITED_SEARCH_STRING))
