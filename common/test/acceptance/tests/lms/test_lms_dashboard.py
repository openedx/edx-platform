# -*- coding: utf-8 -*-
"""
End-to-end tests for the main LMS Dashboard (aka, Student Dashboard).
"""
from ..helpers import UniqueCourseTest
from ...fixtures.course import CourseFixture
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.dashboard import DashboardPage


class BaseLmsDashboardTest(UniqueCourseTest):
    """ Base test suite for the LMS Student Dashboard """

    def setUp(self):
        """
        Initializes the components (page objects, courses, users) for this test suite
        """
        # Some parameters are provided by the parent setUp() routine, such as the following:
        # self.course_id, self.course_info, self.unique_id
        super(BaseLmsDashboardTest, self).setUp()

        # Load page objects for use by the tests
        self.dashboard_page = DashboardPage(self.browser)

        # Configure some aspects of the test course and install the settings into the course
        self.course_fixture = CourseFixture(
            self.course_info["org"],
            self.course_info["number"],
            self.course_info["run"],
            self.course_info["display_name"],
        )
        self.course_fixture.add_advanced_settings({
            u"social_sharing_url": {u"value": "http://custom/course/url"}
        })
        self.course_fixture.install()

        # Create the test user, register them for the course, and authenticate
        self.username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        self.email = "{user}@example.com".format(user=self.username)
        AutoAuthPage(
            self.browser,
            username=self.username,
            email=self.email,
            course_id=self.course_id
        ).visit()

        # Navigate the authenticated, enrolled user to the dashboard page and get testing!
        self.dashboard_page.visit()


class LmsDashboardPageTest(BaseLmsDashboardTest):
    """ Test suite for the LMS Student Dashboard page """

    def test_dashboard_course_listings(self):
        """
        Perform a general validation of the course listings section
        """
        course_listings = self.dashboard_page.get_course_listings()
        self.assertEqual(len(course_listings), 1)

    def test_dashboard_social_sharing_feature(self):
        """
        Validate the behavior of the social sharing feature
        """
        twitter_widget = self.dashboard_page.get_course_social_sharing_widget('twitter')
        twitter_url = "https://twitter.com/intent/tweet?text=Testing+feature%3A%20http%3A%2F%2Fcustom%2Fcourse%2Furl"  # pylint: disable=line-too-long
        self.assertEqual(twitter_widget.attrs('title')[0], 'Share on Twitter')
        self.assertEqual(twitter_widget.attrs('data-tooltip')[0], 'Share on Twitter')
        self.assertEqual(twitter_widget.attrs('aria-haspopup')[0], 'true')
        self.assertEqual(twitter_widget.attrs('aria-expanded')[0], 'false')
        self.assertEqual(twitter_widget.attrs('target')[0], '_blank')
        self.assertIn(twitter_url, twitter_widget.attrs('href')[0])
        self.assertIn(twitter_url, twitter_widget.attrs('onclick')[0])

        facebook_widget = self.dashboard_page.get_course_social_sharing_widget('facebook')
        facebook_url = "https://www.facebook.com/sharer/sharer.php?u=http%3A%2F%2Fcustom%2Fcourse%2Furl"
        self.assertEqual(facebook_widget.attrs('title')[0], 'Share on Facebook')
        self.assertEqual(facebook_widget.attrs('data-tooltip')[0], 'Share on Facebook')
        self.assertEqual(facebook_widget.attrs('aria-haspopup')[0], 'true')
        self.assertEqual(facebook_widget.attrs('aria-expanded')[0], 'false')
        self.assertEqual(facebook_widget.attrs('target')[0], '_blank')
        self.assertIn(facebook_url, facebook_widget.attrs('href')[0])
        self.assertIn(facebook_url, facebook_widget.attrs('onclick')[0])
