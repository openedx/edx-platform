"""
Tests for the recently enrolled messaging within the Dashboard.
"""
import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client
from opaque_keys.edx import locator
from pytz import UTC
import unittest

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.models import CourseEnrollment, DashboardConfiguration
from student.views import get_course_enrollment_pairs, _get_recently_enrolled_courses


class TestRecentEnrollments(ModuleStoreTestCase):
    """
    Unit tests for getting the list of courses for a logged in user
    """
    def setUp(self):
        """
        Add a student
        """
        super(TestRecentEnrollments, self).setUp()
        self.student = UserFactory()

        # Old Course
        old_course_location = locator.CourseLocator('Org0', 'Course0', 'Run0')
        course, enrollment = self._create_course_and_enrollment(old_course_location)
        enrollment.created = datetime.datetime(1900, 12, 31, 0, 0, 0, 0)
        enrollment.save()

        # New Course
        course_location = locator.CourseLocator('Org1', 'Course1', 'Run1')
        self._create_course_and_enrollment(course_location)

    def _create_course_and_enrollment(self, course_location):
        """ Creates a course and associated enrollment. """
        course = CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run
        )
        enrollment = CourseEnrollment.enroll(self.student, course.id)
        return course, enrollment

    def test_recently_enrolled_courses(self):
        """
        Test if the function for filtering recent enrollments works appropriately.
        """
        config = DashboardConfiguration(recent_enrollment_time_delta=60)
        config.save()
        # get courses through iterating all courses
        courses_list = list(get_course_enrollment_pairs(self.student, None, []))
        self.assertEqual(len(courses_list), 2)

        recent_course_list = _get_recently_enrolled_courses(courses_list)
        self.assertEqual(len(recent_course_list), 1)

    def test_zero_second_delta(self):
        """
        Tests that the recent enrollment list is empty if configured to zero seconds.
        """
        config = DashboardConfiguration(recent_enrollment_time_delta=0)
        config.save()
        courses_list = list(get_course_enrollment_pairs(self.student, None, []))
        self.assertEqual(len(courses_list), 2)

        recent_course_list = _get_recently_enrolled_courses(courses_list)
        self.assertEqual(len(recent_course_list), 0)

    def test_enrollments_sorted_most_recent(self):
        """
        Test that the list of newly created courses are properly sorted to show the most
        recent enrollments first.

        """
        config = DashboardConfiguration(recent_enrollment_time_delta=600)
        config.save()

        # Create a number of new enrollments and courses, and force their creation behind
        # the first enrollment
        course_location = locator.CourseLocator('Org2', 'Course2', 'Run2')
        _, enrollment2 = self._create_course_and_enrollment(course_location)
        enrollment2.created = datetime.datetime.now(UTC) - datetime.timedelta(seconds=5)
        enrollment2.save()

        course_location = locator.CourseLocator('Org3', 'Course3', 'Run3')
        _, enrollment3 = self._create_course_and_enrollment(course_location)
        enrollment3.created = datetime.datetime.now(UTC) - datetime.timedelta(seconds=10)
        enrollment3.save()

        course_location = locator.CourseLocator('Org4', 'Course4', 'Run4')
        _, enrollment4 = self._create_course_and_enrollment(course_location)
        enrollment4.created = datetime.datetime.now(UTC) - datetime.timedelta(seconds=15)
        enrollment4.save()

        course_location = locator.CourseLocator('Org5', 'Course5', 'Run5')
        _, enrollment5 = self._create_course_and_enrollment(course_location)
        enrollment5.created = datetime.datetime.now(UTC) - datetime.timedelta(seconds=20)
        enrollment5.save()

        courses_list = list(get_course_enrollment_pairs(self.student, None, []))
        self.assertEqual(len(courses_list), 6)

        recent_course_list = _get_recently_enrolled_courses(courses_list)
        self.assertEqual(len(recent_course_list), 5)

        self.assertEqual(recent_course_list[1][1], enrollment2)
        self.assertEqual(recent_course_list[2][1], enrollment3)
        self.assertEqual(recent_course_list[3][1], enrollment4)
        self.assertEqual(recent_course_list[4][1], enrollment5)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_dashboard_rendering(self):
        """
        Tests that the dashboard renders the recent enrollment messages appropriately.
        """
        config = DashboardConfiguration(recent_enrollment_time_delta=600)
        config.save()
        self.client = Client()
        self.client.login(username=self.student.username, password='test')
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "You have successfully enrolled in")
