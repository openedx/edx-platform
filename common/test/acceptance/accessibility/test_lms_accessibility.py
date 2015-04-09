"""
Single page accessibility tests for LMS.

Note:
    Run with this command `paver test_bokchoy -d accessibility -t test_lms_accessibility`
"""
import os

from ..pages.lms.auto_auth import AutoAuthPage
from ..pages.lms.courseware import CoursewarePage
from ..pages.lms.dashboard import DashboardPage
from ..pages.lms.course_info import CourseInfoPage
from ..pages.lms.login import LoginPage
from ..pages.lms.progress import ProgressPage
from ..pages.common.logout import LogoutPage
from ..fixtures.course import CourseFixture, XBlockFixtureDesc, CourseUpdateDesc
from ..tests.helpers import UniqueCourseTest, load_data_str

from .tenon import AccessibilityTest, TenonIssue


class LmsAccessibilityTest(UniqueCourseTest):
    """
    Base class to capture LMS accessibility scores
    """
    username = 'test_student'
    email = 'student101@example.com'
    key = os.environ.get('TENON_IO_API_KEY', None)

    def setUp(self):
        """
        Setup course
        """
        # First make sure that the tenon.io API key was set
        self.assertIsNotNone(self.key, msg='Please set the OS environment variable TENON_IO_API_KEY to your API key.')

        super(LmsAccessibilityTest, self).setUp()

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_update(CourseUpdateDesc(date='January 29, 2014', content='Test course update1'))
        course_fix.add_update(CourseUpdateDesc(date='January 30, 2014', content='Test course update2'))
        course_fix.add_update(CourseUpdateDesc(date='January 31, 2014', content='Test course update3'))

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=load_data_str('formula_problem.xml')),
                    XBlockFixtureDesc('html', 'Test HTML', data="<html>Html child text</html>"),
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2').add_children(
                    XBlockFixtureDesc('html', 'Html Child', data="<html>Html child text</html>")
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 3').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 3').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 3')
                )
            )
        ).install()

        AutoAuthPage(self.browser, username=self.username, email=self.email, course_id=self.course_id).visit()

    def get_page_issues(self, page):
        """
        Visit a page and run the tenon.io accessibility tests

        Args:
            page (PageObject): page to visit and test

        Returns:
            List of accessibility issues found
        """
        page.visit()
        source = self.browser.page_source
        response = AccessibilityTest(key=self.key, src=source).test_response
        return self.parse_issues(response.result_set)

    @staticmethod
    def parse_issues(result_set):
        """
        Parse the tenon.io result_set to return issues to report

        Args:
            result_set (list of dict): result set from tenon.io response

        Returns:
            List of issues to report for testcase results
        """
        result = []
        for rs in result_set:
            issue = TenonIssue(rs)
            result.append('{} at {}'.format(issue.error_title, issue.xpath))
        return result

    def test_visit_courseware(self):
        courseware_page = CoursewarePage(self.browser, self.course_id)
        issues = self.get_page_issues(courseware_page)
        self.assertEqual([], issues)

    def test_visit_dashboard(self):
        dashboard_page = DashboardPage(self.browser)
        issues = self.get_page_issues(dashboard_page)
        self.assertEqual([], issues)

    def test_visit_course_info(self):
        course_info_page = CourseInfoPage(self.browser, self.course_id)
        issues = self.get_page_issues(course_info_page)
        self.assertEqual([], issues)

    def test_visit_progress_page(self):
        progress_page = ProgressPage(self.browser, self.course_id)
        issues = self.get_page_issues(progress_page)
        self.assertEqual([], issues)
