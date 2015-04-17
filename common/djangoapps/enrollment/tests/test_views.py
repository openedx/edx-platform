"""
Tests for user enrollment.
"""
import json
import unittest

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
from xmodule.modulestore.tests.factories import CourseFactory
from django.test.utils import override_settings

from course_modes.models import CourseMode
from embargo.models import CountryAccessRule, Country, RestrictedCourse
from enrollment.views import EnrollmentUserThrottle
from util.models import RateLimitConfiguration
from util.testing import UrlResetMixin
from enrollment import api
from enrollment.errors import CourseEnrollmentError
from openedx.core.djangoapps.user_api.models import UserOrgTag
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment
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
            mode=CourseMode.HONOR,
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
            'user': username
        }
        if email_opt_in is not None:
            data['email_opt_in'] = email_opt_in

        extra = {}
        if as_server:
            extra['HTTP_X_EDX_API_KEY'] = self.API_KEY

        url = reverse('courseenrollments')
        response = self.client.post(url, json.dumps(data), content_type='application/json', **extra)
        self.assertEqual(response.status_code, expected_status)

        if expected_status in [status.HTTP_200_OK, status.HTTP_200_OK]:
            data = json.loads(response.content)
            self.assertEqual(course_id, data['course_details']['course_id'])
            self.assertEqual(mode, data['mode'])
            self.assertTrue(data['is_active'])

        return response


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

    def setUp(self):
        """ Create a course and user, then log in. """
        super(EnrollmentTest, self).setUp()

        self.rate_limit_config = RateLimitConfiguration.current()
        self.rate_limit_config.enabled = False
        self.rate_limit_config.save()

        throttle = EnrollmentUserThrottle()
        self.rate_limit, rate_duration = throttle.parse_rate(throttle.rate)

        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.other_user = UserFactory.create()
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that users are automatically enrolled as "honor".
        ([], CourseMode.HONOR),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as "honor" by default.
        ([CourseMode.HONOR, CourseMode.VERIFIED, CourseMode.AUDIT], CourseMode.HONOR),
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
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
        )
        # Create an enrollment
        self.assert_enrollment_status()
        resp = self.client.get(
            reverse('courseenrollment', kwargs={'username': self.user.username, "course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual(CourseMode.HONOR, data['mode'])
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
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
        )
        # Create an enrollment
        self.assert_enrollment_status()
        resp = self.client.get(
            reverse('courseenrollment', kwargs={"course_id": unicode(self.course.id)})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.course.id), data['course_details']['course_id'])
        self.assertEqual(CourseMode.HONOR, data['mode'])
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
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
        )
        self.assert_enrollment_status(username=self.other_user.username, expected_status=status.HTTP_404_NOT_FOUND)
        # Verify that the server still has access to this endpoint.
        self.client.logout()
        self.assert_enrollment_status(username=self.other_user.username, as_server=True)

    def test_user_does_not_match_param_for_list(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
        )
        resp = self.client.get(reverse('courseenrollments'), {'user': self.other_user.username})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        # Verify that the server still has access to this endpoint.
        self.client.logout()
        resp = self.client.get(
            reverse('courseenrollments'), {'username': self.other_user.username}, **{'HTTP_X_EDX_API_KEY': self.API_KEY}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_does_not_match_param(self):
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
        )
        url = reverse('courseenrollment',
                      kwargs={'username': self.other_user.username, "course_id": unicode(self.course.id)})

        resp = self.client.get(url)

        # Verify that the server still has access to this endpoint.
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.client.logout()
        resp = self.client.get(url, **{'HTTP_X_EDX_API_KEY': self.API_KEY})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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

    def test_with_invalid_course_id(self):
        self.assert_enrollment_status(course_id='entirely/fake/course', expected_status=status.HTTP_400_BAD_REQUEST)

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
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
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
            mode_slug=CourseMode.HONOR,
            mode_display_name=CourseMode.HONOR,
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

    def test_update_enrollment_with_mode(self):
        """With the right API key, update an existing enrollment with a new mode. """
        # Create an honor and verified mode for a course. This allows an update.
        for mode in [CourseMode.HONOR, CourseMode.VERIFIED]:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode,
                mode_display_name=mode,
            )

        # Create an enrollment
        self.assert_enrollment_status(as_server=True)

        # Check that the enrollment is honor.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.HONOR)

        # Check that the enrollment upgraded to verified.
        self.assert_enrollment_status(as_server=True, mode=CourseMode.VERIFIED, expected_status=status.HTTP_200_OK)
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.VERIFIED)

    def test_downgrade_enrollment_with_mode(self):
        """With the right API key, downgrade an existing enrollment with a new mode. """
        # Create an honor and verified mode for a course. This allows an update.
        for mode in [CourseMode.HONOR, CourseMode.VERIFIED]:
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

        # Check that the enrollment downgraded to honor.
        self.assert_enrollment_status(as_server=True, mode=CourseMode.HONOR, expected_status=status.HTTP_200_OK)
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.HONOR)

    def test_change_mode_from_user(self):
        """Users should not be able to alter the enrollment mode on an enrollment. """
        # Create an honor and verified mode for a course. This allows an update.
        for mode in [CourseMode.HONOR, CourseMode.VERIFIED]:
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
        self.assertEqual(course_mode, CourseMode.HONOR)

        # Get a 403 response when trying to upgrade yourself.
        self.assert_enrollment_status(mode=CourseMode.VERIFIED, expected_status=status.HTTP_403_FORBIDDEN)
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, CourseMode.HONOR)

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

    def assert_access_denied(self, user_message_url):
        """
        Verify that the view returns HTTP status 403 and includes a URL in the response, and no enrollment is created.
        """
        data = self._generate_data()
        response = self.client.post(self.url, data, content_type='application/json')

        # Expect an error response
        self.assertEqual(response.status_code, 403)

        # Expect that the redirect URL is included in the response
        resp_data = json.loads(response.content)
        self.assertEqual(resp_data['user_message_url'], user_message_url)

        # Verify that we were not enrolled
        self.assertEqual(self._get_enrollments(), [])

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_change_enrollment_restrict_geoip(self):
        """ Validates that enrollment changes are blocked if the request originates from an embargoed country. """

        # Use the helper to setup the embargo and simulate a request from a blocked IP address.
        with restrict_course(self.course.id) as redirect_url:
            self.assert_access_denied(redirect_url)

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

        user_message_url = reverse('embargo_blocked_message',
                                   kwargs={'access_point': 'enrollment', 'message_key': 'default'})
        self.assert_access_denied(user_message_url)

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
        self.assertEqual(resp.status_code, 401)

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
