"""
Test courseware search
"""
import os
import json

from ...pages.common.logout import LogoutPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.lms.courseware_search import CoursewareSearchPage
from ...pages.lms.course_nav import CourseNavPage
from ...fixtures.course import XBlockFixtureDesc
from ..helpers import create_user_partition_json

from xmodule.partitions.partitions import Group

from nose.plugins.attrib import attr

from ..studio.base_studio_test import ContainerBase

from ...pages.studio.auto_auth import AutoAuthPage as StudioAutoAuthPage


@attr('shard_1')
class SplitTestCoursewareSearchTest(ContainerBase):
    """
    Test courseware search on Split Test Module.
    """
    USERNAME = 'STUDENT_TESTER'
    EMAIL = 'student101@example.com'

    TEST_INDEX_FILENAME = "test_root/index_file.dat"

    def setUp(self, is_staff=True):
        """
        Create search page and course content to search
        """
        # create test file in which index for this test will live
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)

        super(SplitTestCoursewareSearchTest, self).setUp(is_staff=is_staff)
        self.staff_user = self.user

        self.courseware_search_page = CoursewareSearchPage(self.browser, self.course_id)
        self.course_navigation_page = CourseNavPage(self.browser)
        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self._add_and_configure_split_test()
        self._studio_reindex()

    def tearDown(self):
        super(SplitTestCoursewareSearchTest, self).tearDown()
        os.remove(self.TEST_INDEX_FILENAME)

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        LogoutPage(self.browser).visit()
        StudioAutoAuthPage(self.browser, username=username, email=email,
                           course_id=self.course_id, staff=staff).visit()

    def _studio_reindex(self):
        """
        Reindex course content on studio course page
        """
        self._auto_auth(self.staff_user["username"], self.staff_user["email"], True)
        self.course_outline.visit()
        self.course_outline.start_reindex()
        self.course_outline.wait_for_ajax()

    def _add_and_configure_split_test(self):
        """
        Add a split test and a configuration to a test course fixture
        """
        # Create a new group configurations
        # pylint: disable=W0212
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        "Name",
                        "Description.",
                        [Group("0", "Group A"), Group("1", "Group B")]
                    ),
                    create_user_partition_json(
                        456,
                        "Name 2",
                        "Description 2.",
                        [Group("2", "Group C"), Group("3", "Group D")]
                    ),
                ],
            },
        })

        # Add a split test module to the 'Test Unit' vertical in the course tree
        split_test_1 = XBlockFixtureDesc('split_test', 'Test Content Experiment 1', metadata={'user_partition_id': 0})
        split_test_1_parent_vertical = self.course_fixture.get_nested_xblocks(category="vertical")[1]
        self.course_fixture.create_xblock(split_test_1_parent_vertical.locator, split_test_1)

        # Add a split test module to the 'Test 2 Unit' vertical in the course tree
        split_test_2 = XBlockFixtureDesc('split_test', 'Test Content Experiment 2', metadata={'user_partition_id': 456})
        split_test_2_parent_vertical = self.course_fixture.get_nested_xblocks(category="vertical")[2]
        self.course_fixture.create_xblock(split_test_2_parent_vertical.locator, split_test_2)

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        course_fixture.add_advanced_settings({
            u"advanced_modules": {"value": ["split_test"]},
        })

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Content Section').add_children(
                XBlockFixtureDesc('sequential', 'Content Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Content Unit').add_children(
                        XBlockFixtureDesc('html', 'VISIBLETOALLCONTENT', data='<html>VISIBLETOALLCONTENT</html>')
                    )
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            ),
            XBlockFixtureDesc('chapter', 'X Section').add_children(
                XBlockFixtureDesc('sequential', 'X Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'X Unit')
                )
            ),
        )

        self.test_1_breadcrumb = "Test Section \xe2\x96\xb8 Test Subsection \xe2\x96\xb8 Test Unit".decode("utf-8")
        self.test_2_breadcrumb = "X Section \xe2\x96\xb8 X Subsection \xe2\x96\xb8 X Unit".decode("utf-8")

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()

    def test_search_for_experiment_content_user_not_assigned(self):
        """
        Test user can't search for experiment content if not assigned to a group.
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()
        self.courseware_search_page.search_for_term("Group")
        assert "Sorry, no results were found." in self.courseware_search_page.search_results.html[0]

    def test_search_for_experiment_content_user_assigned_to_one_group(self):
        """
        Test user can search for experiment content restricted to his group
        when assigned to just one experiment group
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()
        self.course_navigation_page.go_to_section("Test Section", "Test Subsection")
        self.courseware_search_page.search_for_term("Group")
        assert "1 result" in self.courseware_search_page.search_results.html[0]
        assert self.test_1_breadcrumb in self.courseware_search_page.search_results.html[0]
        assert self.test_2_breadcrumb not in self.courseware_search_page.search_results.html[0]
