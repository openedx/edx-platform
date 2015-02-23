"""
Tests for user enrollment.
"""
import ddt
import json
import unittest

from mock import patch
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from util.testing import UrlResetMixin
from enrollment import api
from enrollment.errors import CourseEnrollmentError
from openedx.core.djangoapps.user_api.models import UserOrgTag
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment
from embargo.test_utils import restrict_course


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentTest(ModuleStoreTestCase, APITestCase):
    """
    Test user enrollment, especially with different course modes.
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

    def test_check_enrollment(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )
        # Create an enrollment
        self._create_enrollment()
        resp = self.client.get(
            reverse('courseenrollment', kwargs={"user": self.user.username, "course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual('honor', data['mode'])
        self.assertTrue(data['is_active'])

    @ddt.data(
        (True, u"True"),
        (False, u"False"),
        (None, None)
    )
    @ddt.unpack
    def test_email_opt_in_true(self, opt_in, pref_value):
        """
        Verify that the email_opt_in parameter sets the underlying flag.
        And that if the argument is not present, then it does not affect the flag
        """
        def _assert_no_opt_in_set():
            """ Check the tag doesn't exit"""
            with self.assertRaises(UserOrgTag.DoesNotExist):
                UserOrgTag.objects.get(user=self.user, org=self.course.id.org, key="email-optin")

        _assert_no_opt_in_set()
        self._create_enrollment(email_opt_in=opt_in)
        if opt_in is None:
            _assert_no_opt_in_set()
        else:
            preference = UserOrgTag.objects.get(user=self.user, org=self.course.id.org, key="email-optin")
            self.assertEquals(preference.value, pref_value)

    def test_enroll_prof_ed(self):
        # Create the prod ed mode.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='professional',
            mode_display_name='Professional Education',
        )

        # Enroll in the course, this will fail if the mode is not explicitly professional.
        resp = self._create_enrollment(expected_status=status.HTTP_400_BAD_REQUEST)

        # While the enrollment wrong is invalid, the response content should have
        # all the valid enrollment modes.
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual(1, len(data['course_details']['course_modes']))
        self.assertEqual('professional', data['course_details']['course_modes'][0]['slug'])

    def test_user_not_specified(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )
        # Create an enrollment
        self._create_enrollment()
        resp = self.client.get(
            reverse('courseenrollment', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual('honor', data['mode'])
        self.assertTrue(data['is_active'])

    def test_user_not_authenticated(self):
        # Log out, so we're no longer authenticated
        self.client.logout()

        # Try to enroll, this should fail.
        self._create_enrollment(expected_status=status.HTTP_403_FORBIDDEN)

    def test_user_not_activated(self):
        # Log out the default user, Bob.
        self.client.logout()

        # Create a user account
        self.user = UserFactory.create(
            username="inactive",
            email="inactive@example.com",
            password=self.PASSWORD,
            is_active=True
        )

        # Log in with the unactivated account
        self.client.login(username="inactive", password=self.PASSWORD)

        # Deactivate the user. Has to be done after login to get the user into the
        # request and properly logged in.
        self.user.is_active = False
        self.user.save()

        # Enrollment should succeed, even though we haven't authenticated.
        self._create_enrollment()

    def test_user_does_not_match_url(self):
        # Try to enroll a user that is not the authenticated user.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )
        self._create_enrollment(username='not_the_user', expected_status=status.HTTP_404_NOT_FOUND)

    def test_user_does_not_match_param_for_list(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )
        resp = self.client.get(reverse('courseenrollments'), {"user": "not_the_user"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_does_not_match_param(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )
        resp = self.client.get(
            reverse('courseenrollment', kwargs={"user": "not_the_user", "course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_course_details(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor',
        )
        resp = self.client.get(
            reverse('courseenrollmentdetails', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_id'])

    def test_with_invalid_course_id(self):
        self._create_enrollment(course_id='entirely/fake/course', expected_status=status.HTTP_400_BAD_REQUEST)

    def test_get_enrollment_details_bad_course(self):
        resp = self.client.get(
            reverse('courseenrollmentdetails', kwargs={"course_id": "some/fake/course"})
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch.object(api, "get_enrollment")
    def test_get_enrollment_internal_error(self, mock_get_enrollment):
        mock_get_enrollment.side_effect = CourseEnrollmentError("Something bad happened.")
        resp = self.client.get(
            reverse('courseenrollment', kwargs={"user": self.user.username, "course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def _create_enrollment(self, course_id=None, username=None, expected_status=status.HTTP_200_OK, email_opt_in=None):
        """Enroll in the course and verify the URL we are sent to. """
        course_id = unicode(self.course.id) if course_id is None else course_id
        username = self.user.username if username is None else username

        params = {
            'course_details': {
                'course_id': course_id
            },
            'user': username
        }
        if email_opt_in is not None:
            params['email_opt_in'] = email_opt_in
        resp = self.client.post(reverse('courseenrollments'), params, format='json')
        self.assertEqual(resp.status_code, expected_status)

        if expected_status == status.HTTP_200_OK:
            data = json.loads(resp.content)
            self.assertEqual(course_id, data['course_details']['course_id'])
            self.assertEqual('honor', data['mode'])
            self.assertTrue(data['is_active'])
        return resp

    def test_enrollment_already_enrolled(self):
        response = self._create_enrollment()
        repeat_response = self._create_enrollment()
        self.assertEqual(json.loads(response.content), json.loads(repeat_response.content))

    def test_get_enrollment_with_invalid_key(self):
        resp = self.client.post(
            reverse('courseenrollments'),
            {
                'course_details': {
                    'course_id': 'invalidcourse'
                },
                'user': self.user.username
            },
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No course ", resp.content)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentEmbargoTest(UrlResetMixin, ModuleStoreTestCase):
    """Test that enrollment is blocked from embargoed countries. """

    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    @patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    def setUp(self):
        """ Create a course and user, then log in. """
        super(EnrollmentEmbargoTest, self).setUp('embargo')
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    def test_embargo_change_enrollment_restrict(self):
        url = reverse('courseenrollments')
        data = json.dumps({
            'course_details': {
                'course_id': unicode(self.course.id)
            },
            'user': self.user.username
        })

        # Attempt to enroll from a country embargoed for this course
        with restrict_course(self.course.id) as redirect_url:
            response = self.client.post(url, data, content_type='application/json')

            # Expect an error response
            self.assertEqual(response.status_code, 403)

            # Expect that the redirect URL is included in the response
            resp_data = json.loads(response.content)
            self.assertEqual(resp_data['user_message_url'], redirect_url)

        # Verify that we were not enrolled
        self.assertEqual(self._get_enrollments(), [])

    @patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    def test_embargo_change_enrollment_allow(self):
        url = reverse('courseenrollments')
        data = json.dumps({
            'course_details': {
                'course_id': unicode(self.course.id)
            },
            'user': self.user.username
        })

        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify that we were enrolled
        self.assertEqual(len(self._get_enrollments()), 1)

    def _get_enrollments(self):
        """Retrieve the enrollment list for the current user. """
        url = reverse('courseenrollments')
        resp = self.client.get(url)
        return json.loads(resp.content)
