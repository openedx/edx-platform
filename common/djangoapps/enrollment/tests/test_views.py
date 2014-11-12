"""
Tests for student enrollment.
"""
import ddt
import json
import unittest

from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment

# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentTest(ModuleStoreTestCase, APITestCase):
    """
    Test student enrollment, especially with different course modes.
    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    def setUp(self):
        """ Create a course and user, then log in. """
        super(EnrollmentTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that users are automatically enrolled as "honor".
        ([], 'honor'),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as "honor" by default.
        (['honor', 'verified', 'audit'], 'honor'),
    )
    @ddt.unpack
    def test_enroll(self, course_modes, enrollment_mode):
        # Create the course modes (if any) required for this test case
        for mode_slug in course_modes:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode_slug,
                mode_display_name=mode_slug,
            )

        # Create an enrollment
        self._create_enrollment()

        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, enrollment_mode)

    def test_enroll_prof_ed(self):
        # Create the prod ed mode.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='professional',
            mode_display_name='Professional Education',
        )

        # Enroll in the course, this will fail if the mode is not explicitly professional.
        resp = self.client.post(reverse('courseenrollment', kwargs={'course_id': (unicode(self.course.id))}))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # While the enrollment wrong is invalid, the response content should have
        # all the valid enrollment modes.
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_id'])
        self.assertEqual(1, len(data['course_modes']))
        self.assertEqual('professional', data['course_modes'][0]['slug'])

    def test_unenroll(self):
        # Create a course mode.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )

        # Create an enrollment
        resp = self._create_enrollment()

        # Deactivate the enrollment in the course and verify the URL we get sent to
        resp = self.client.post(reverse(
            'courseenrollment',
            kwargs={'course_id': (unicode(self.course.id))}
        ), {'deactivate': True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course']['course_id'])
        self.assertEqual('honor', data['mode'])
        self.assertFalse(data['is_active'])

    def test_user_not_authenticated(self):
        # Log out, so we're no longer authenticated
        self.client.logout()

        # Try to enroll, this should fail.
        resp = self.client.post(reverse('courseenrollment', kwargs={'course_id': (unicode(self.course.id))}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_activated(self):
        # Create a user account, but don't activate it
        self.user = UserFactory.create(
            username="inactive",
            email="inactive@example.com",
            password=self.PASSWORD,
            is_active=False
        )

        # Log in with the unactivated account
        self.client.login(username="inactive", password=self.PASSWORD)

        # Enrollment should succeed, even though we haven't authenticated.
        resp = self.client.post(reverse('courseenrollment', kwargs={'course_id': (unicode(self.course.id))}))
        self.assertEqual(resp.status_code, 200)

    def test_unenroll_not_enrolled_in_course(self):
        # Deactivate the enrollment in the course and verify the URL we get sent to
        resp = self.client.post(reverse(
            'courseenrollment',
            kwargs={'course_id': (unicode(self.course.id))}
        ), {'deactivate': True})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_enrollment_mode(self):
        # Request an enrollment with verified mode, which does not exist for this course.
        resp = self.client.post(reverse(
            'courseenrollment',
            kwargs={'course_id': (unicode(self.course.id))}),
            {'mode': 'verified'}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_id'])
        self.assertEqual('honor', data['course_modes'][0]['slug'])

    def test_with_invalid_course_id(self):
        # Create an enrollment
        resp = self.client.post(reverse('courseenrollment', kwargs={'course_id': 'entirely/fake/course'}))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def _create_enrollment(self):
        """Enroll in the course and verify the URL we are sent to. """
        resp = self.client.post(reverse('courseenrollment', kwargs={'course_id': (unicode(self.course.id))}))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course']['course_id'])
        self.assertEqual('honor', data['mode'])
        self.assertTrue(data['is_active'])
        return resp
