"""
Tests for user enrollment.
"""
import json
import itertools
import unittest
import datetime

import ddt
from django.core.cache import cache
from mock import patch
from django.test import Client
from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls_range
from django.test.utils import override_settings
import pytz

from course_modes.models import CourseMode
from embargo.models import CountryAccessRule, Country, RestrictedCourse
from enrollment.views import EnrollmentUserThrottle
from util.models import RateLimitConfiguration
from util.testing import UrlResetMixin
from enrollment import api
from enrollment.errors import CourseEnrollmentError
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.user_api.models import UserOrgTag
from openedx.core.lib.django_test_client_utils import get_absolute_url
from student.models import CourseEnrollment
from student.roles import CourseStaffRole
from student.tests.factories import AdminFactory, CourseModeFactory, UserFactory
from embargo.test_utils import restrict_course


class EnrollmentTestMixin(object):
    """ Mixin with methods useful for testing enrollments. """
    API_KEY = "i am a key"

    def assert_enrollment_status(
            self,
            course_id=None,
            username=None,
            expected_status=status.HTTP_200_OK,
            email_opt_in=None,
            as_server=False,
            mode=CourseMode.DEFAULT_MODE_SLUG,
            is_active=None,
            enrollment_attributes=None,
            min_mongo_calls=0,
            max_mongo_calls=0,
    ):
        """
        Enroll in the course and verify the response's status code. If the expected status is 200, also validates
        the response content.

        Returns
            Response
        """
        course_id = course_id or unicode(self.course.id)
        username = username or self.user.username

        data = {
            'mode': mode,
            'course_details': {
                'course_id': course_id
            },
            'user': username,
            'enrollment_attributes': enrollment_attributes
        }

        if is_active is not None:
            data['is_active'] = is_active

        if email_opt_in is not None:
            data['email_opt_in'] = email_opt_in

        extra = {}
        if as_server:
            extra['HTTP_X_EDX_API_KEY'] = self.API_KEY

        # Verify that the modulestore is queried as expected.
        with check_mongo_calls_range(min_finds=min_mongo_calls, max_finds=max_mongo_calls):
            with patch('enrollment.views.audit_log') as mock_audit_log:
                url = reverse('courseenrollments')
                response = self.client.post(url, json.dumps(data), content_type='application/json', **extra)
                self.assertEqual(response.status_code, expected_status)

                if expected_status == status.HTTP_200_OK:
                    data = json.loads(response.content)
                    self.assertEqual(course_id, data['course_details']['course_id'])

                    if mode is not None:
                        self.assertEqual(mode, data['mode'])

                    if is_active is not None:
                        self.assertEqual(is_active, data['is_active'])
                    else:
                        self.assertTrue(data['is_active'])

                    if as_server:
                        # Verify that an audit message was logged.
                        self.assertTrue(mock_audit_log.called)

                        # If multiple enrollment calls are made in the scope of a
                        # single test, we want to validate that audit messages are
                        # logged for each call.
                        mock_audit_log.reset_mock()

        return response

    def assert_enrollment_activation(self, expected_activation, expected_mode):
        """Change an enrollment's activation and verify its activation and mode are as expected."""
        self.assert_enrollment_status(
            as_server=True,
            mode=expected_mode,
            is_active=expected_activation,
            expected_status=status.HTTP_200_OK
        )
        actual_mode, actual_activation = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertEqual(actual_activation, expected_activation)
        self.assertEqual(actual_mode, expected_mode)


@override_settings(EDX_API_KEY="i am a key")
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentTest(EnrollmentTestMixin, ModuleStoreTestCase, APITestCase):
    """
    Test user enrollment, especially with different course modes.
    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    OTHER_USERNAME = "Jane"
    OTHER_EMAIL = "jane@example.com"

    def setUp(self):
        """ Create a course and user, then log in. """
        super(EnrollmentTest, self).setUp()

        self.rate_limit_config = RateLimitConfiguration.current()
        self.rate_limit_config.enabled = False
        self.rate_limit_config.save()

        throttle = EnrollmentUserThrottle()
        self.rate_limit, rate_duration = throttle.parse_rate(throttle.rate)

        # Pass emit_signals when creating the course so it would be cached
        # as a CourseOverview.
        self.course = CourseFactory.create(emit_signals=True)

        self.user = UserFactory.create(
            username=self.USERNAME,
            email=self.EMAIL,
            password=self.PASSWORD,
        )
        self.other_user = UserFactory.create(
            username=self.OTHER_USERNAME,
            email=self.OTHER_EMAIL,
            password=self.PASSWORD,
        )
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that users are automatically enrolled as the default
        ([], CourseMode.DEFAULT_MODE_SLUG),

        # Audit / Verified
        # We should always go to the "choose your course" page.
        # We should also be enrolled as the default.
        ([CourseMode.VERIFIED, CourseMode.AUDIT], CourseMode.DEFAULT_MODE_SLUG),
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
        self.assert_enrollment_status()

        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, enrollment_mode)

    def test_check_enrollment(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
        )
        # Create an enrollment
        self.assert_enrollment_status()
        resp = self.client.get(
            reverse('courseenrollment', kwargs={'username': self.user.username, "course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual(CourseMode.DEFAULT_MODE_SLUG, data['mode'])
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
        self.assert_enrollment_status(email_opt_in=opt_in)
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
        resp = self.assert_enrollment_status(expected_status=status.HTTP_400_BAD_REQUEST)

        # While the enrollment wrong is invalid, the response content should have
        # all the valid enrollment modes.
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual(1, len(data['course_details']['course_modes']))
        self.assertEqual('professional', data['course_details']['course_modes'][0]['slug'])

    def test_user_not_specified(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
        )
        # Create an enrollment
        self.assert_enrollment_status()
        resp = self.client.get(
            reverse('courseenrollment', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual(CourseMode.DEFAULT_MODE_SLUG, data['mode'])
        self.assertTrue(data['is_active'])

    def test_user_not_authenticated(self):
        # Log out, so we're no longer authenticated
        self.client.logout()

        # Try to enroll, this should fail.
        self.assert_enrollment_status(expected_status=status.HTTP_401_UNAUTHORIZED)

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
        self.assert_enrollment_status()

    def test_user_does_not_match_url(self):
        # Try to enroll a user that is not the authenticated user.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
        )
        self.assert_enrollment_status(username=self.other_user.username, expected_status=status.HTTP_404_NOT_FOUND)
        # Verify that the server still has access to this endpoint.
        self.client.logout()
        self.assert_enrollment_status(username=self.other_user.username, as_server=True)

    def _assert_enrollments_visible_in_list(self, courses, use_server_key=False):
        """
        Check that the list of enrollments of self.user returned for the currently logged in user
        matches the list of courses passed in in 'courses'.
        """
        kwargs = {}
        if use_server_key:
            kwargs.update(HTTP_X_EDX_API_KEY=self.API_KEY)
        response = self.client.get(reverse('courseenrollments'), {'user': self.user.username}, **kwargs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertItemsEqual(
            [enrollment['course_details']['course_id'] for enrollment in data],
            [unicode(course.id) for course in courses]
        )

    def test_enrollment_list_permissions(self):
        """
        Test that the correct list of enrollments is returned, depending on the permissions of the
        requesting user.
        """
        # Create another course, and enroll self.user in both courses.
        other_course = CourseFactory.create(emit_signals=True)
        for course in self.course, other_course:
            CourseModeFactory.create(
                course_id=unicode(course.id),
                mode_slug=CourseMode.DEFAULT_MODE_SLUG,
                mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
            )
            self.assert_enrollment_status(
                course_id=unicode(course.id),
                max_mongo_calls=0,
            )
        # Verify the user himself can see both of his enrollments.
        self._assert_enrollments_visible_in_list([self.course, other_course])
        # Verify that self.other_user can't see any of the enrollments.
        self.client.login(username=self.OTHER_USERNAME, password=self.PASSWORD)
        self._assert_enrollments_visible_in_list([])
        # Create a staff user for self.course (but nor for other_course) and log her in.
        staff_user = UserFactory.create(username='staff', email='staff@example.com', password=self.PASSWORD)
        CourseStaffRole(self.course.id).add_users(staff_user)
        self.client.login(username='staff', password=self.PASSWORD)
        # Verify that she can see only the enrollment in the course she has staff privileges for.
        self._assert_enrollments_visible_in_list([self.course])
        # Create a global staff user, and verify she can see all enrollments.
        AdminFactory(username='global_staff', email='global_staff@example.com', password=self.PASSWORD)
        self.client.login(username='global_staff', password=self.PASSWORD)
        self._assert_enrollments_visible_in_list([self.course, other_course])
        # Verify the server can see all enrollments.
        self.client.logout()
        self._assert_enrollments_visible_in_list([self.course, other_course], use_server_key=True)

    def test_user_does_not_match_param(self):
        """
        The view should return status 404 if the enrollment username does not match the username of the user
        making the request, unless the request is made by a superuser or with a server API key.
        """
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
        )
        url = reverse('courseenrollment',
                      kwargs={'username': self.other_user.username, "course_id": unicode(self.course.id)})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify that the server still has access to this endpoint.
        self.client.logout()
        response = self.client.get(url, **{'HTTP_X_EDX_API_KEY': self.API_KEY})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify superusers have access to this endpoint
        superuser = UserFactory.create(password=self.PASSWORD, is_superuser=True)
        self.client.login(username=superuser.username, password=self.PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_course_details(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
            sku='123',
        )
        resp = self.client.get(
            reverse('courseenrollmentdetails', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_id'])
        mode = data['course_modes'][0]
        self.assertEqual(mode['slug'], CourseMode.HONOR)
        self.assertEqual(mode['sku'], '123')
        self.assertEqual(mode['name'], CourseMode.HONOR)

    def test_get_course_details_with_credit_course(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.CREDIT_MODE,
            mode_display_name=CourseMode.CREDIT_MODE,
        )
        resp = self.client.get(
            reverse('courseenrollmentdetails', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_id'])
        mode = data['course_modes'][0]
        self.assertEqual(mode['slug'], CourseMode.CREDIT_MODE)
        self.assertEqual(mode['name'], CourseMode.CREDIT_MODE)

    @ddt.data(
        # NOTE: Studio requires a start date, but this is not
        # enforced at the data layer, so we need to handle the case
        # in which no dates are specified.
        (None, None, None, None),
        (datetime.datetime(2015, 1, 2, 3, 4, 5), None, "2015-01-02T03:04:05Z", None),
        (None, datetime.datetime(2015, 1, 2, 3, 4, 5), None, "2015-01-02T03:04:05Z"),
        (datetime.datetime(2014, 6, 7, 8, 9, 10), datetime.datetime(2015, 1, 2, 3, 4, 5), "2014-06-07T08:09:10Z", "2015-01-02T03:04:05Z"),
    )
    @ddt.unpack
    def test_get_course_details_course_dates(self, start_datetime, end_datetime, expected_start, expected_end):
        course = CourseFactory.create(start=start_datetime, end=end_datetime)
        # Load a CourseOverview. This initial load should result in a cache
        # miss; the modulestore is queried and course metadata is cached.
        __ = CourseOverview.get_from_id(course.id)

        self.assert_enrollment_status(course_id=unicode(course.id))

        # Check course details
        url = reverse('courseenrollmentdetails', kwargs={"course_id": unicode(course.id)})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = json.loads(resp.content)
        self.assertEqual(data['course_start'], expected_start)
        self.assertEqual(data['course_end'], expected_end)

        # Check enrollment course details
        url = reverse('courseenrollment', kwargs={"course_id": unicode(course.id)})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = json.loads(resp.content)
        self.assertEqual(data['course_details']['course_start'], expected_start)
        self.assertEqual(data['course_details']['course_end'], expected_end)

        # Check enrollment list course details
        resp = self.client.get(reverse('courseenrollments'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = json.loads(resp.content)
        self.assertEqual(data[0]['course_details']['course_start'], expected_start)
        self.assertEqual(data[0]['course_details']['course_end'], expected_end)

    def test_with_invalid_course_id(self):
        self.assert_enrollment_status(
            course_id='entirely/fake/course',
            expected_status=status.HTTP_400_BAD_REQUEST,
            min_mongo_calls=3,
            max_mongo_calls=4
        )

    def test_get_enrollment_details_bad_course(self):
        resp = self.client.get(
            reverse('courseenrollmentdetails', kwargs={"course_id": "some/fake/course"})
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch.object(api, "get_enrollment")
    def test_get_enrollment_internal_error(self, mock_get_enrollment):
        mock_get_enrollment.side_effect = CourseEnrollmentError("Something bad happened.")
        resp = self.client.get(
            reverse('courseenrollment', kwargs={'username': self.user.username, "course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enrollment_already_enrolled(self):
        response = self.assert_enrollment_status()
        repeat_response = self.assert_enrollment_status(expected_status=status.HTTP_200_OK)
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

    def test_enrollment_throttle_for_user(self):
        """Make sure a user requests do not exceed the maximum number of requests"""
        self.rate_limit_config.enabled = True
        self.rate_limit_config.save()
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
        )

        for attempt in xrange(self.rate_limit + 10):
            expected_status = status.HTTP_429_TOO_MANY_REQUESTS if attempt >= self.rate_limit else status.HTTP_200_OK
            self.assert_enrollment_status(expected_status=expected_status)

    def test_enrollment_throttle_for_service(self):
        """Make sure a service can call the enrollment API as many times as needed. """
        self.rate_limit_config.enabled = True
        self.rate_limit_config.save()
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
        )

        for attempt in xrange(self.rate_limit + 10):
            self.assert_enrollment_status(as_server=True)

    def test_create_enrollment_with_mode(self):
        """With the right API key, create a new enrollment with a mode set other than the default."""
        # Create a professional ed course mode.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='professional',
            mode_display_name='professional',
        )

        # Create an enrollment
        self.assert_enrollment_status(as_server=True, mode='professional')

        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, 'professional')

    def test_enrollment_includes_expired_verified(self):
        """With the right API key, request that expired course verifications are still returned. """
        # Create a honor mode for a course.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
        )

        # Create a verified mode for a course.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            mode_display_name=CourseMode.VERIFIED,
            expiration_datetime='1970-01-01 05:00:00'
        )

        # Passes the include_expired parameter to the API call
        v_response = self.client.get(
            reverse('courseenrollmentdetails', kwargs={"course_id": unicode(self.course.id)}), {'include_expired': True}
        )
        v_data = json.loads(v_response.content)

        # Ensure that both course modes are returned
        self.assertEqual(len(v_data['course_modes']), 2)

        # Omits the include_expired parameter from the API call
        h_response = self.client.get(reverse('courseenrollmentdetails', kwargs={"course_id": unicode(self.course.id)}))
        h_data = json.loads(h_response.content)

        # Ensure that only one course mode is returned and that it is honor
        self.assertEqual(len(h_data['course_modes']), 1)
        self.assertEqual(h_data['course_modes'][0]['slug'], CourseMode.HONOR)

    def test_update_enrollment_with_mode(self):
        """With the right API key, update an existing enrollment with a new mode. """
        # Create an honor and verified mode for a course. This allows an update.
        for mode in [CourseMode.DEFAULT_MODE_SLUG, CourseMode.VERIFIED]:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create an enrollment
        self.assert_enrollment_status(as_server=True)

        # Check that the enrollment is default.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.DEFAULT_MODE_SLUG)

        # Check that the enrollment upgraded to verified.
        self.assert_enrollment_status(as_server=True, mode=CourseMode.VERIFIED, expected_status=status.HTTP_200_OK)
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.VERIFIED)

    def test_enrollment_with_credit_mode(self):
        """With the right API key, update an existing enrollment with credit
        mode and set enrollment attributes.
        """
        for mode in [CourseMode.DEFAULT_MODE_SLUG, CourseMode.CREDIT_MODE]:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create an enrollment
        self.assert_enrollment_status(as_server=True)

        # Check that the enrollment is the default.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.DEFAULT_MODE_SLUG)

        # Check that the enrollment upgraded to credit.
        enrollment_attributes = [{
            "namespace": "credit",
            "name": "provider_id",
            "value": "hogwarts",
        }]
        self.assert_enrollment_status(
            as_server=True,
            mode=CourseMode.CREDIT_MODE,
            expected_status=status.HTTP_200_OK,
            enrollment_attributes=enrollment_attributes
        )
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.CREDIT_MODE)

    def test_enrollment_with_invalid_attr(self):
        """Check response status is bad request when invalid enrollment
        attributes are passed
        """
        for mode in [CourseMode.DEFAULT_MODE_SLUG, CourseMode.CREDIT_MODE]:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create an enrollment
        self.assert_enrollment_status(as_server=True)

        # Check that the enrollment is the default.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.DEFAULT_MODE_SLUG)

        # Check that the enrollment upgraded to credit.
        enrollment_attributes = [{
            "namespace": "credit",
            "name": "invalid",
            "value": "hogwarts",
        }]
        self.assert_enrollment_status(
            as_server=True,
            mode=CourseMode.CREDIT_MODE,
            expected_status=status.HTTP_400_BAD_REQUEST,
            enrollment_attributes=enrollment_attributes
        )
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.DEFAULT_MODE_SLUG)

    def test_downgrade_enrollment_with_mode(self):
        """With the right API key, downgrade an existing enrollment with a new mode. """
        # Create an honor and verified mode for a course. This allows an update.
        for mode in [CourseMode.DEFAULT_MODE_SLUG, CourseMode.VERIFIED]:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create a 'verified' enrollment
        self.assert_enrollment_status(as_server=True, mode=CourseMode.VERIFIED)

        # Check that the enrollment is verified.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.VERIFIED)

        # Check that the enrollment was downgraded to the default mode.
        self.assert_enrollment_status(
            as_server=True,
            mode=CourseMode.DEFAULT_MODE_SLUG,
            expected_status=status.HTTP_200_OK
        )
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.DEFAULT_MODE_SLUG)

    @ddt.data(
        ((CourseMode.DEFAULT_MODE_SLUG, ), CourseMode.DEFAULT_MODE_SLUG),
        ((CourseMode.DEFAULT_MODE_SLUG, CourseMode.VERIFIED), CourseMode.DEFAULT_MODE_SLUG),
        ((CourseMode.DEFAULT_MODE_SLUG, CourseMode.VERIFIED), CourseMode.VERIFIED),
        ((CourseMode.PROFESSIONAL, ), CourseMode.PROFESSIONAL),
        ((CourseMode.NO_ID_PROFESSIONAL_MODE, ), CourseMode.NO_ID_PROFESSIONAL_MODE),
        ((CourseMode.VERIFIED, CourseMode.CREDIT_MODE), CourseMode.VERIFIED),
        ((CourseMode.VERIFIED, CourseMode.CREDIT_MODE), CourseMode.CREDIT_MODE),
    )
    @ddt.unpack
    def test_deactivate_enrollment(self, configured_modes, selected_mode):
        """With the right API key, deactivate (i.e., unenroll from) an existing enrollment."""
        # Configure a set of modes for the course.
        for mode in configured_modes:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create an enrollment with the selected mode.
        self.assert_enrollment_status(as_server=True, mode=selected_mode)

        # Check that the enrollment has the correct mode and is active.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, selected_mode)

        # Verify that a non-Boolean enrollment status is treated as invalid.
        self.assert_enrollment_status(
            as_server=True,
            mode=None,
            is_active='foo',
            expected_status=status.HTTP_400_BAD_REQUEST
        )

        # Verify that the enrollment has been deactivated, and that the mode is unchanged.
        self.assert_enrollment_activation(False, selected_mode)

        # Verify that enrollment deactivation is idempotent.
        self.assert_enrollment_activation(False, selected_mode)

        # Verify that omitting the mode returns 400 for course configurations
        # in which the default mode doesn't exist.
        expected_status = (
            status.HTTP_200_OK
            if CourseMode.DEFAULT_MODE_SLUG in configured_modes
            else status.HTTP_400_BAD_REQUEST
        )
        self.assert_enrollment_status(
            as_server=True,
            is_active=False,
            expected_status=expected_status,
        )

    def test_deactivate_enrollment_expired_mode(self):
        """Verify that an enrollment in an expired mode can be deactivated."""
        for mode in (CourseMode.HONOR, CourseMode.VERIFIED):
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create verified enrollment.
        self.assert_enrollment_status(as_server=True, mode=CourseMode.VERIFIED)

        # Change verified mode expiration.
        mode = CourseMode.objects.get(course_id=self.course.id, mode_slug=CourseMode.VERIFIED)
        mode.expiration_datetime = datetime.datetime(year=1970, month=1, day=1, tzinfo=pytz.utc)
        mode.save()

        # Deactivate enrollment.
        self.assert_enrollment_activation(False, CourseMode.VERIFIED)

    def test_change_mode_from_user(self):
        """Users should not be able to alter the enrollment mode on an enrollment. """
        # Create a default and a verified mode for a course. This allows an update.
        for mode in [CourseMode.DEFAULT_MODE_SLUG, CourseMode.VERIFIED]:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create an enrollment
        self.assert_enrollment_status()

        # Check that the enrollment is honor.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.DEFAULT_MODE_SLUG)

        # Get a 403 response when trying to upgrade yourself.
        self.assert_enrollment_status(mode=CourseMode.VERIFIED, expected_status=status.HTTP_403_FORBIDDEN)
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.DEFAULT_MODE_SLUG)

    @ddt.data(*itertools.product(
        (CourseMode.HONOR, CourseMode.VERIFIED),
        (CourseMode.HONOR, CourseMode.VERIFIED),
        (True, False),
        (True, False),
    ))
    @ddt.unpack
    def test_change_mode_from_server(self, old_mode, new_mode, old_is_active, new_is_active):
        """
        Server-to-server calls should be allowed to change the mode of any
        enrollment, as long as the enrollment is not being deactivated during
        the same call (this is assumed to be an error on the client's side).
        """
        for mode in [CourseMode.HONOR, CourseMode.VERIFIED]:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Set up the initial enrollment
        self.assert_enrollment_status(as_server=True, mode=old_mode, is_active=old_is_active)
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertEqual(is_active, old_is_active)
        self.assertEqual(course_mode, old_mode)

        expected_status = status.HTTP_400_BAD_REQUEST if (
            old_mode != new_mode and
            old_is_active != new_is_active and
            not new_is_active
        ) else status.HTTP_200_OK

        # simulate the server-server api call under test
        response = self.assert_enrollment_status(
            as_server=True,
            mode=new_mode,
            is_active=new_is_active,
            expected_status=expected_status,
        )

        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        if expected_status == status.HTTP_400_BAD_REQUEST:
            # nothing should have changed
            self.assertEqual(is_active, old_is_active)
            self.assertEqual(course_mode, old_mode)
            # error message should contain specific text.  Otto checks for this text in the message.
            self.assertRegexpMatches(json.loads(response.content)['message'], 'Enrollment mode mismatch')
        else:
            # call should have succeeded
            self.assertEqual(is_active, new_is_active)
            self.assertEqual(course_mode, new_mode)

    def test_change_mode_invalid_user(self):
        """
        Attempts to change an enrollment for a non-existent user should result in an HTTP 404 for non-server users,
        and HTTP 406 for server users.
        """
        self.assert_enrollment_status(username='fake-user', expected_status=status.HTTP_404_NOT_FOUND, as_server=False)
        self.assert_enrollment_status(username='fake-user', expected_status=status.HTTP_406_NOT_ACCEPTABLE,
                                      as_server=True)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentEmbargoTest(EnrollmentTestMixin, UrlResetMixin, ModuleStoreTestCase):
    """Test that enrollment is blocked from embargoed countries. """

    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        """ Create a course and user, then log in. """
        super(EnrollmentEmbargoTest, self).setUp('embargo')

        self.course = CourseFactory.create()
        # Load a CourseOverview. This initial load should result in a cache
        # miss; the modulestore is queried and course metadata is cached.
        __ = CourseOverview.get_from_id(self.course.id)

        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.url = reverse('courseenrollments')

    def _generate_data(self):
        return json.dumps({
            'course_details': {
                'course_id': unicode(self.course.id)
            },
            'user': self.user.username
        })

    def assert_access_denied(self, user_message_path):
        """
        Verify that the view returns HTTP status 403 and includes a URL in the response, and no enrollment is created.
        """
        data = self._generate_data()
        response = self.client.post(self.url, data, content_type='application/json')

        # Expect an error response
        self.assertEqual(response.status_code, 403)

        # Expect that the redirect URL is included in the response
        resp_data = json.loads(response.content)
        user_message_url = get_absolute_url(user_message_path)
        self.assertEqual(resp_data['user_message_url'], user_message_url)

        # Verify that we were not enrolled
        self.assertEqual(self._get_enrollments(), [])

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_change_enrollment_restrict_geoip(self):
        """ Validates that enrollment changes are blocked if the request originates from an embargoed country. """

        # Use the helper to setup the embargo and simulate a request from a blocked IP address.
        with restrict_course(self.course.id) as redirect_path:
            self.assert_access_denied(redirect_path)

    def _setup_embargo(self):
        restricted_course = RestrictedCourse.objects.create(course_key=self.course.id)

        restricted_country = Country.objects.create(country='US')
        unrestricted_country = Country.objects.create(country='CA')

        CountryAccessRule.objects.create(
            rule_type=CountryAccessRule.BLACKLIST_RULE,
            restricted_course=restricted_course,
            country=restricted_country
        )

        # Clear the cache to remove the effects of previous embargo tests
        cache.clear()

        return unrestricted_country, restricted_country

    @override_settings(EDX_API_KEY=EnrollmentTestMixin.API_KEY)
    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_change_enrollment_restrict_user_profile(self):
        """ Validates that enrollment changes are blocked if the user's profile is linked to an embargoed country. """

        __, restricted_country = self._setup_embargo()

        # Update the user's profile, linking the user to the embargoed country.
        self.user.profile.country = restricted_country.country
        self.user.profile.save()

        path = reverse('embargo_blocked_message', kwargs={'access_point': 'enrollment', 'message_key': 'default'})
        self.assert_access_denied(path)

    @override_settings(EDX_API_KEY=EnrollmentTestMixin.API_KEY)
    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_change_enrollment_allow_user_profile(self):
        """
        Validates that enrollment changes are allowed if the user's profile is NOT linked to an embargoed country.
        """

        # Setup the embargo
        unrestricted_country, __ = self._setup_embargo()

        # Verify that users without black-listed country codes *can* be enrolled
        self.user.profile.country = unrestricted_country.country
        self.user.profile.save()
        self.assert_enrollment_status()

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_change_enrollment_allow(self):
        self.assert_enrollment_status()

        # Verify that we were enrolled
        self.assertEqual(len(self._get_enrollments()), 1)

    def _get_enrollments(self):
        """Retrieve the enrollment list for the current user. """
        resp = self.client.get(self.url)
        return json.loads(resp.content)


def cross_domain_config(func):
    """Decorator for configuring a cross-domain request. """
    feature_flag_decorator = patch.dict(settings.FEATURES, {
        'ENABLE_CORS_HEADERS': True,
        'ENABLE_CROSS_DOMAIN_CSRF_COOKIE': True
    })
    settings_decorator = override_settings(
        CORS_ORIGIN_WHITELIST=["www.edx.org"],
        CROSS_DOMAIN_CSRF_COOKIE_NAME="prod-edx-csrftoken",
        CROSS_DOMAIN_CSRF_COOKIE_DOMAIN=".edx.org"
    )
    is_secure_decorator = patch.object(WSGIRequest, 'is_secure', return_value=True)

    return feature_flag_decorator(
        settings_decorator(
            is_secure_decorator(func)
        )
    )


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentCrossDomainTest(ModuleStoreTestCase):
    """Test cross-domain calls to the enrollment end-points. """

    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"
    REFERER = "https://www.edx.org"

    def setUp(self):
        """ Create a course and user, then log in. """
        super(EnrollmentCrossDomainTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        self.client = Client(enforce_csrf_checks=True)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @cross_domain_config
    def test_cross_domain_change_enrollment(self, *args):  # pylint: disable=unused-argument
        csrf_cookie = self._get_csrf_cookie()
        resp = self._cross_domain_post(csrf_cookie)

        # Expect that the request gets through successfully,
        # passing the CSRF checks (including the referer check).
        self.assertEqual(resp.status_code, 200)

    @cross_domain_config
    def test_cross_domain_missing_csrf(self, *args):  # pylint: disable=unused-argument
        resp = self._cross_domain_post('invalid_csrf_token')
        self.assertEqual(resp.status_code, 403)

    def _get_csrf_cookie(self):
        """Retrieve the cross-domain CSRF cookie. """
        url = reverse('courseenrollment', kwargs={
            'course_id': unicode(self.course.id)
        })
        resp = self.client.get(url, HTTP_REFERER=self.REFERER)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('prod-edx-csrftoken', resp.cookies)  # pylint: disable=no-member
        return resp.cookies['prod-edx-csrftoken'].value  # pylint: disable=no-member

    def _cross_domain_post(self, csrf_cookie):
        """Perform a cross-domain POST request. """
        url = reverse('courseenrollments')
        params = json.dumps({
            'course_details': {
                'course_id': unicode(self.course.id),
            },
            'user': self.user.username
        })
        return self.client.post(
            url, params, content_type='application/json',
            HTTP_REFERER=self.REFERER,
            HTTP_X_CSRFTOKEN=csrf_cookie
        )
