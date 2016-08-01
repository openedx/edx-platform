"""
Test courseware search
"""

import json

from common.test.acceptance.tests.helpers import remove_file
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.pages.lms.courseware_search import CoursewareSearchPage
from common.test.acceptance.pages.lms.course_nav import CourseNavPage
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.tests.helpers import create_user_partition_json

from xmodule.partitions.partitions import Group

from nose.plugins.attrib import attr

from common.test.acceptance.tests.studio.base_studio_test import ContainerBase

from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage as StudioAutoAuthPage


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
        self.addCleanup(remove_file, self.TEST_INDEX_FILENAME)

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

        self._create_group_configuration()
        self._studio_reindex()

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

    def _create_group_configuration(self):
        """
        Create a group configuration for course
        """
        # pylint: disable=protected-access
        self.course_fixture._update_xblock(self.course_fixture._course_location, {
            "metadata": {
                u"user_partitions": [
                    create_user_partition_json(
                        0,
                        "Configuration A/B",
                        "Content Group Partition.",
                        [Group("0", "Group A"), Group("1", "Group B")]
                    )
                ]
            }
        })

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        course_fixture.add_advanced_settings({
            u"advanced_modules": {"value": ["split_test"]},
        })

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc(
                            'html',
                            'VISIBLE TO A',
                            data='<html>VISIBLE TO A</html>',
                            metadata={"group_access": {0: [0]}}
                        ),
                        XBlockFixtureDesc(
                            'html',
                            'VISIBLE TO B',
                            data='<html>VISIBLE TO B</html>',
                            metadata={"group_access": {0: [1]}}
                        )
                    )
                )
            )
        )

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()

    def test_search_for_experiment_content_user_assigned_to_one_group(self):
        """
        Test user can search for experiment content restricted to his group
        when assigned to just one experiment group
        """
        self._auto_auth(self.USERNAME, self.EMAIL, False)
        self.courseware_search_page.visit()
        self.courseware_search_page.search_for_term("VISIBLE TO")
        assert "1 result" in self.courseware_search_page.search_results.html[0]
