"""
Acceptance tests for Studio related to course reruns.
"""

import random
from bok_choy.promise import EmptyPromise
from nose.tools import assert_in

from ...pages.studio.index import DashboardPage
from ...pages.studio.course_rerun import CourseRerunPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.lms.courseware import CoursewarePage
from ...fixtures.course import XBlockFixtureDesc

from base_studio_test import StudioCourseTest


class CourseRerunTest(StudioCourseTest):
    """
    Feature: Courses can be rerun
    """

    __test__ = True

    SECTION_NAME = 'Rerun Section'
    SUBSECITON_NAME = 'Rerun Subsection'
    UNIT_NAME = 'Rerun Unit'
    COMPONENT_NAME = 'Rerun Component'
    COMPONENT_CONTENT = 'Test Content'

    def setUp(self):
        """
        Login as global staff because that's the only way to rerun a course.
        """
        super(CourseRerunTest, self).setUp(is_staff=True)
        self.dashboard_page = DashboardPage(self.browser)

    def populate_course_fixture(self, course_fixture):
        """
        Create a sample course with one section, one subsection, one unit, and one component.
        """
        course_fixture.add_children(
            XBlockFixtureDesc('chapter', self.SECTION_NAME).add_children(
                XBlockFixtureDesc('sequential', self.SUBSECITON_NAME).add_children(
                    XBlockFixtureDesc('vertical', self.UNIT_NAME).add_children(
                        XBlockFixtureDesc('html', self.COMPONENT_NAME, self.COMPONENT_CONTENT)
                    )
                )
            )
        )

    def test_course_rerun(self):
        """
        Scenario: Courses can be rerun
            Given I have a course with a section, subsesction, vertical, and html component with content 'Test Content'
            When I visit the course rerun page
            And I type 'test_rerun' in the course run field
            And I click Create Rerun
            And I visit the course listing page
            And I wait for all courses to finish processing
            And I click on the course with run 'test_rerun'
            Then I see a rerun notification on the course outline page
            And when I click 'Dismiss' on the notification
            Then I do not see a rerun notification
            And when I expand the subsection and click on the unit
            And I click 'View Live Version'
            Then I see one html component with the content 'Test Content'
        """
        course_info = (self.course_info['org'], self.course_info['number'], self.course_info['run'])
        updated_course_info = course_info[0] + "+" + course_info[1] + "+" + course_info[2]

        self.dashboard_page.visit()
        self.dashboard_page.create_rerun(updated_course_info)

        rerun_page = CourseRerunPage(self.browser, *course_info)
        rerun_page.wait_for_page()
        course_run = 'test_rerun_' + str(random.randrange(1000000, 9999999))
        rerun_page.course_run = course_run
        rerun_page.create_rerun()

        def finished_processing():
            self.dashboard_page.visit()
            return not self.dashboard_page.has_processing_courses

        EmptyPromise(finished_processing, "Rerun finished processing", try_interval=5, timeout=60).fulfill()

        assert_in(course_run, self.dashboard_page.course_runs)
        self.dashboard_page.click_course_run(course_run)

        outline_page = CourseOutlinePage(self.browser, *course_info)
        outline_page.wait_for_page()
        self.assertTrue(outline_page.has_rerun_notification)

        outline_page.dismiss_rerun_notification()
        EmptyPromise(lambda: not outline_page.has_rerun_notification, "Rerun notification dismissed").fulfill()

        subsection = outline_page.section(self.SECTION_NAME).subsection(self.SUBSECITON_NAME)
        subsection.expand_subsection()
        unit_page = subsection.unit(self.UNIT_NAME).go_to()

        unit_page.view_published_version()
        courseware = CoursewarePage(self.browser, self.course_id)
        courseware.wait_for_page()
        self.assertEqual(courseware.num_xblock_components, 1)
        self.assertEqual(courseware.xblock_component_html_content(), self.COMPONENT_CONTENT)
