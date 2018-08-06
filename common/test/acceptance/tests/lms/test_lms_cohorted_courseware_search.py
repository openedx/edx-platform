"""
Test courseware search
"""

import json
import uuid

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.lms.course_home import CourseHomePage
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.pages.lms.staff_view import StaffCoursewarePage
from common.test.acceptance.pages.studio.xblock_editor import XBlockVisibilityEditorView
from common.test.acceptance.pages.studio.overview import CourseOutlinePage as StudioCourseOutlinePage
from common.test.acceptance.pages.studio.settings_group_configurations import GroupConfigurationsPage
from common.test.acceptance.tests.discussion.helpers import CohortTestMixin
from common.test.acceptance.tests.helpers import remove_file
from common.test.acceptance.tests.studio.base_studio_test import ContainerBase


class CoursewareSearchCohortTest(ContainerBase, CohortTestMixin):
    """
    Test courseware search.
    """
    shard = 1
    TEST_INDEX_FILENAME = "test_root/index_file.dat"

    def setUp(self, is_staff=True):
        """
        Create search page and course content to search
        """
        # create test file in which index for this test will live
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)
        self.addCleanup(remove_file, self.TEST_INDEX_FILENAME)

        super(CoursewareSearchCohortTest, self).setUp(is_staff=is_staff)
        self.staff_user = self.user

        self.studio_course_outline = StudioCourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.content_group_a = "Content Group A"
        self.content_group_b = "Content Group B"

        # Create a student who will be in "Cohort A"
        self.cohort_a_student_username = "cohort_a_" + str(uuid.uuid4().hex)[:12]
        self.cohort_a_student_email = self.cohort_a_student_username + "@example.com"
        AutoAuthPage(
            self.browser, username=self.cohort_a_student_username, email=self.cohort_a_student_email, no_login=True
        ).visit()

        # Create a student who will be in "Cohort B"
        self.cohort_b_student_username = "cohort_b_" + str(uuid.uuid4().hex)[:12]
        self.cohort_b_student_email = self.cohort_b_student_username + "@example.com"
        AutoAuthPage(
            self.browser, username=self.cohort_b_student_username, email=self.cohort_b_student_email, no_login=True
        ).visit()

        # Create a student who will end up in the default cohort group
        self.cohort_default_student_username = "cohort_default_student"
        self.cohort_default_student_email = "cohort_default_student@example.com"
        AutoAuthPage(
            self.browser, username=self.cohort_default_student_username,
            email=self.cohort_default_student_email, no_login=True
        ).visit()

        self.course_home_page = CourseHomePage(self.browser, self.course_id)

        # Enable Cohorting and assign cohorts and content groups
        self._auto_auth(self.staff_user["username"], self.staff_user["email"], True)
        self.enable_cohorting(self.course_fixture)
        self.create_content_groups()
        self.link_html_to_content_groups_and_publish()
        self.create_cohorts_and_assign_students()

        self._studio_reindex()

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, username=username, email=email,
                     course_id=self.course_id, staff=staff).visit()

    def _studio_reindex(self):
        """
        Reindex course content on studio course page
        """
        self._auto_auth(self.staff_user["username"], self.staff_user["email"], True)
        self.studio_course_outline.visit()
        self.studio_course_outline.start_reindex()
        self.studio_course_outline.wait_for_ajax()

    def _goto_staff_page(self):
        """
        Open staff page with assertion
        """
        self.course_home_page.visit()
        self.course_home_page.resume_course_from_header()
        staff_page = StaffCoursewarePage(self.browser, self.course_id)
        self.assertEqual(staff_page.staff_view_mode, 'Staff')
        return staff_page

    def _search_for_term(self, term):
        """
        Search for term in course and return results.
        """
        self.course_home_page.visit()
        course_search_results_page = self.course_home_page.search_for_term(term)
        results = course_search_results_page.search_results.html
        return results[0] if len(results) > 0 else []

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        self.group_a_html = 'GROUPACONTENT'
        self.group_b_html = 'GROUPBCONTENT'
        self.group_a_and_b_html = 'GROUPAANDBCONTENT'
        self.visible_to_all_html = 'VISIBLETOALLCONTENT'

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('html', self.group_a_html, data='<html>GROUPACONTENT</html>'),
                        XBlockFixtureDesc('html', self.group_b_html, data='<html>GROUPBCONTENT</html>'),
                        XBlockFixtureDesc('html', self.group_a_and_b_html, data='<html>GROUPAANDBCONTENT</html>'),
                        XBlockFixtureDesc('html', self.visible_to_all_html, data='<html>VISIBLETOALLCONTENT</html>')
                    )
                )
            )
        )

    def create_content_groups(self):
        """
        Creates two content groups in Studio Group Configurations Settings.
        """
        group_configurations_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        group_configurations_page.visit()

        group_configurations_page.create_first_content_group()
        config = group_configurations_page.content_groups[0]
        config.name = self.content_group_a
        config.save()

        group_configurations_page.add_content_group()
        config = group_configurations_page.content_groups[1]
        config.name = self.content_group_b
        config.save()

    def link_html_to_content_groups_and_publish(self):
        """
        Updates 3 of the 4 existing html to limit their visibility by content group.
        Publishes the modified units.
        """
        container_page = self.go_to_unit_page()

        def set_visibility(html_block_index, groups):
            """
            Set visibility on html blocks to specified groups.
            """
            html_block = container_page.xblocks[html_block_index]
            html_block.edit_visibility()
            visibility_dialog = XBlockVisibilityEditorView(self.browser, html_block.locator)
            visibility_dialog.select_groups_in_partition_scheme(visibility_dialog.CONTENT_GROUP_PARTITION, groups)

        set_visibility(1, [self.content_group_a])
        set_visibility(2, [self.content_group_b])
        set_visibility(3, [self.content_group_a, self.content_group_b])

        container_page.publish_action.click()

    def create_cohorts_and_assign_students(self):
        """
        Adds 2 manual cohorts, linked to content groups, to the course.
        Each cohort is assigned one student.
        """
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        cohort_management_page = instructor_dashboard_page.select_cohort_management()

        def add_cohort_with_student(cohort_name, content_group, student):
            """
            Create cohort and assign student to it.
            """
            cohort_management_page.add_cohort(cohort_name, content_group=content_group)
            cohort_management_page.add_students_to_selected_cohort([student])
        add_cohort_with_student("Cohort A", self.content_group_a, self.cohort_a_student_username)
        add_cohort_with_student("Cohort B", self.content_group_b, self.cohort_b_student_username)
        cohort_management_page.wait_for_ajax()

    def test_cohorted_search_user_a_a_content(self):
        """
        Test user can search content restricted to his cohort.
        """
        self._auto_auth(self.cohort_a_student_username, self.cohort_a_student_email, False)
        search_results = self._search_for_term(self.group_a_html)
        assert self.group_a_html in search_results

    def test_cohorted_search_user_b_a_content(self):
        """
        Test user can not search content restricted to his cohort.
        """
        self._auto_auth(self.cohort_b_student_username, self.cohort_b_student_email, False)
        search_results = self._search_for_term(self.group_a_html)
        assert self.group_a_html not in search_results

    def test_cohorted_search_user_staff_all_content(self):
        """
        Test staff user can search all public content if cohorts used on course.
        """
        self._auto_auth(self.staff_user["username"], self.staff_user["email"], False)
        self._goto_staff_page().set_staff_view_mode('Staff')
        search_results = self._search_for_term(self.visible_to_all_html)
        assert self.visible_to_all_html in search_results
        search_results = self._search_for_term(self.group_a_and_b_html)
        assert self.group_a_and_b_html in search_results
        search_results = self._search_for_term(self.group_a_html)
        assert self.group_a_html in search_results
        search_results = self._search_for_term(self.group_b_html)
        assert self.group_b_html in search_results

    def test_cohorted_search_user_staff_masquerade_student_content(self):
        """
        Test staff user can search just student public content if selected from preview menu.

        NOTE: Although it would be wise to combine these masquerading tests into
        a single test due to expensive setup, doing so revealed a very low
        priority bug where searching seems to stick/cache the access of the
        first user who searches for future searches.

        """
        self._auto_auth(self.staff_user["username"], self.staff_user["email"], False)
        self._goto_staff_page().set_staff_view_mode('Learner')
        search_results = self._search_for_term(self.visible_to_all_html)
        assert self.visible_to_all_html in search_results
        search_results = self._search_for_term(self.group_a_and_b_html)
        assert self.group_a_and_b_html not in search_results
        search_results = self._search_for_term(self.group_a_html)
        assert self.group_a_html not in search_results
        search_results = self._search_for_term(self.group_b_html)
        assert self.group_b_html not in search_results

    def test_cohorted_search_user_staff_masquerade_cohort_content(self):
        """
        Test staff user can search cohort and public content if selected from preview menu.
        """
        self._auto_auth(self.staff_user["username"], self.staff_user["email"], False)
        self._goto_staff_page().set_staff_view_mode('Learner in ' + self.content_group_a)
        search_results = self._search_for_term(self.visible_to_all_html)
        assert self.visible_to_all_html in search_results
        search_results = self._search_for_term(self.group_a_and_b_html)
        assert self.group_a_and_b_html in search_results
        search_results = self._search_for_term(self.group_a_html)
        assert self.group_a_html in search_results
        search_results = self._search_for_term(self.group_b_html)
        assert self.group_b_html not in search_results
