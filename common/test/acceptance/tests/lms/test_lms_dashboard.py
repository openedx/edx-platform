# -*- coding: utf-8 -*-
"""
End-to-end tests for the main LMS Dashboard (aka, Student Dashboard).
"""

import six

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.dashboard import DashboardPage
from common.test.acceptance.tests.helpers import UniqueCourseTest, generate_course_key

DEFAULT_SHORT_DATE_FORMAT = u'{dt:%b} {dt.day}, {dt.year}'
TEST_DATE_FORMAT = u'{dt:%b} {dt.day}, {dt.year} {dt.hour:02}:{dt.minute:02}'


class BaseLmsDashboardTestMultiple(UniqueCourseTest):
    """ Base test suite for the LMS Student Dashboard with Multiple Courses"""

    def setUp(self):
        """
        Initializes the components (page objects, courses, users) for this test suite
        """
        # Some parameters are provided by the parent setUp() routine, such as the following:
        # self.course_id, self.course_info, self.unique_id
        super(BaseLmsDashboardTestMultiple, self).setUp()

        # Load page objects for use by the tests
        self.dashboard_page = DashboardPage(self.browser)

        # Configure some aspects of the test course and install the settings into the course
        self.courses = {
            'A': {
                'org': 'test_org',
                'number': self.unique_id,
                'run': 'test_run_A',
                'display_name': 'Test Course A',
                'enrollment_mode': 'audit',
                'cert_name_long': 'Certificate of Audit Achievement'
            },
            'B': {
                'org': 'test_org',
                'number': self.unique_id,
                'run': 'test_run_B',
                'display_name': 'Test Course B',
                'enrollment_mode': 'verified',
                'cert_name_long': 'Certificate of Verified Achievement'
            },
            'C': {
                'org': 'test_org',
                'number': self.unique_id,
                'run': 'test_run_C',
                'display_name': 'Test Course C',
                'enrollment_mode': 'credit',
                'cert_name_long': 'Certificate of Credit Achievement'
            }
        }

        self.username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        self.email = "{user}@example.com".format(user=self.username)

        self.course_keys = {}
        self.course_fixtures = {}

        for key, value in six.iteritems(self.courses):
            course_key = generate_course_key(
                value['org'],
                value['number'],
                value['run'],
            )

            course_fixture = CourseFixture(
                value['org'],
                value['number'],
                value['run'],
                value['display_name'],
            )

            course_fixture.add_advanced_settings({
                u"social_sharing_url": {u"value": "http://custom/course/url"},
                u"cert_name_long": {u"value": value['cert_name_long']}
            })
            course_fixture.add_children(
                XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                    XBlockFixtureDesc('sequential', 'Test Subsection 1,1').add_children(
                        XBlockFixtureDesc('problem', 'Test Problem 1', data='<problem>problem 1 dummy body</problem>'),
                        XBlockFixtureDesc('html', 'html 1', data="<html>html 1 dummy body</html>"),
                        XBlockFixtureDesc('problem', 'Test Problem 2', data="<problem>problem 2 dummy body</problem>"),
                        XBlockFixtureDesc('html', 'html 2', data="<html>html 2 dummy body</html>"),
                    ),
                    XBlockFixtureDesc('sequential', 'Test Subsection 1,2').add_children(
                        XBlockFixtureDesc('problem', 'Test Problem 3', data='<problem>problem 3 dummy body</problem>'),
                    ),
                    XBlockFixtureDesc(
                        'sequential', 'Test HIDDEN Subsection', metadata={'visible_to_staff_only': True}
                    ).add_children(
                        XBlockFixtureDesc('problem', 'Test HIDDEN Problem', data='<problem>hidden problem</problem>'),
                    ),
                )
            ).install()

            self.course_keys[key] = course_key
            self.course_fixtures[key] = course_fixture

            # Create the test user, register them for the course, and authenticate
            AutoAuthPage(
                self.browser,
                username=self.username,
                email=self.email,
                course_id=course_key,
                enrollment_mode=value['enrollment_mode']
            ).visit()

        # Navigate the authenticated, enrolled user to the dashboard page and get testing!
        self.dashboard_page.visit()


class LmsDashboardA11yTest(BaseLmsDashboardTestMultiple):
    """
    Class to test lms student dashboard accessibility.
    """
    a11y = True

    def test_dashboard_course_listings_a11y(self):
        """
        Test the accessibility of the course listings
        """
        self.dashboard_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'button-name',  # TODO: AC-935
                'landmark-no-duplicate-banner',  # TODO: AC-934
                'landmark-complementary-is-top-level',  # TODO: AC-939
                'region'  # TODO: AC-932
            ]
        })
        course_listings = self.dashboard_page.get_courses()
        self.assertEqual(len(course_listings), 3)
        self.dashboard_page.a11y_audit.check_for_accessibility_errors()
