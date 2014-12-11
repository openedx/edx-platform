"""
Tests for student enrollment.
"""
from datetime import datetime
import ddt
import pytz
import unittest
from mock import patch

from django.test.utils import override_settings
from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse
from xmodule.modulestore.django import modulestore
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
class EnrollmentTest(ModuleStoreTestCase):
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

        self.urls = [
            reverse('course_modes_choose', kwargs={'course_id': unicode(self.course.id)})
        ]

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that we're redirected to the dashboard
        # and automatically enrolled as "honor"
        ([], '', 'honor'),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as "honor" by default.
        (['honor', 'verified', 'audit'], 'course_modes_choose', 'honor'),

        # Professional ed
        # Expect that we're sent to the "choose your track" page
        # (which will, in turn, redirect us to a page where we can verify/pay)
        # We should NOT be auto-enrolled, because that would be giving
        # away an expensive course for free :)
        (['professional'], 'course_modes_choose', None),
    )
    @ddt.unpack
    def test_enroll(self, course_modes, next_url, enrollment_mode):
        # Create the course modes (if any) required for this test case
        for mode_slug in course_modes:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode_slug,
                mode_display_name=mode_slug,
            )

        # Reverse the expected next URL, if one is provided
        # (otherwise, use an empty string, which the JavaScript client
        # interprets as a redirect to the dashboard)
        full_url = (
            reverse(next_url, kwargs={'course_id': unicode(self.course.id)})
            if next_url else next_url
        )

        # Enroll in the course and verify the URL we get sent to
        resp = self._change_enrollment('enroll')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, full_url)

        # If we're not expecting to be enrolled, verify that this is the case
        if enrollment_mode is None:
            self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

        # Otherwise, verify that we're enrolled with the expected course mode
        else:
            self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
            course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
            self.assertTrue(is_active)
            self.assertEqual(course_mode, enrollment_mode)

    def _create_about_item(self, about_key):
        """Create specified about item. Uses key as the data."""
        store = modulestore()
        about_item = store.create_xblock(self.course.runtime, self.course.id, 'about', about_key, {'data': about_key})
        store.update_item(about_item, self.user.id, allow_not_found=True)

    def assertEnrollmentEmail(self, expected_subject, expected_msg):
        """Assert that enrollment email was sent with expected subject and msg."""
        self.course.enable_enrollment_email = True
        self.course = self.update_course(self.course, self.user.id)
        call_command('loaddata', 'course_email_template.json')

        with patch('django.contrib.auth.models.User.email_user') as mock_email_user:
            resp = self._change_enrollment('enroll')
            self.assertEqual(resp.status_code, 200)
            (subject, msg, from_addr) = mock_email_user.call_args[0]
            self.assertEquals(subject, expected_subject)
            self.assertIn(expected_msg, msg)
            self.assertEquals(from_addr, settings.DEFAULT_FROM_EMAIL)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_AUTH_FOR_TESTING': False})
    def test_pre_enrollment_email(self):
        """
        Test sending automated emails to users upon course enrollment before it starts.
        """
        self._create_about_item('pre_enrollment_email_subject')
        self._create_about_item('pre_enrollment_email')

        self.assertEnrollmentEmail('pre_enrollment_email_subject', 'pre_enrollment_email')

    @patch.dict(settings.FEATURES, {'AUTOMATIC_AUTH_FOR_TESTING': False})
    def test_post_enrollment_email(self):
        """
        Test sending automated emails to users upon course enrollment after it starts.
        """
        self.course.start = datetime.now(pytz.UTC)
        self._create_about_item('post_enrollment_email_subject')
        self._create_about_item('post_enrollment_email')

        self.assertEnrollmentEmail('post_enrollment_email_subject', 'post_enrollment_email')

    @patch.dict(settings.FEATURES, {'AUTOMATIC_AUTH_FOR_TESTING': False})
    @patch('student.views.log.error')
    def test_enrollment_email_failure(self, error_log):
        """
        Test that enrollment email failure logs an error
        """
        self.course.enable_enrollment_email = True
        self.course = self.update_course(self.course, self.user.id)
        call_command('loaddata', 'course_email_template.json')

        with patch('django.contrib.auth.models.User.email_user', side_effect=Exception):
            resp = self._change_enrollment('enroll')
            self.assertEqual(resp.status_code, 200)
            error_log.assert_called_with('Unable to send course enrollment verification email to user from "{from_address}"'.format(
                from_address=settings.DEFAULT_FROM_EMAIL), exc_info=True)

    def test_unenroll(self):
        # Enroll the student in the course
        CourseEnrollment.enroll(self.user, self.course.id, mode="honor")

        # Attempt to unenroll the student
        resp = self._change_enrollment('unenroll')
        self.assertEqual(resp.status_code, 200)

        # Expect that we're no longer enrolled
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_EMAIL_OPT_IN': True})
    @patch('openedx.core.djangoapps.user_api.api.profile.update_email_opt_in')
    @ddt.data(
        ([], 'true'),
        ([], 'false'),
        ([], None),
        (['honor', 'verified'], 'true'),
        (['honor', 'verified'], 'false'),
        (['honor', 'verified'], None),
        (['professional'], 'true'),
        (['professional'], 'false'),
        (['professional'], None),
    )
    @ddt.unpack
    def test_enroll_with_email_opt_in(self, course_modes, email_opt_in, mock_update_email_opt_in):
        # Create the course modes (if any) required for this test case
        for mode_slug in course_modes:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode_slug,
                mode_display_name=mode_slug,
            )

        # Enroll in the course
        self._change_enrollment('enroll', email_opt_in=email_opt_in)

        # Verify that the profile API has been called as expected
        if email_opt_in is not None:
            opt_in = email_opt_in == 'true'
            mock_update_email_opt_in.assert_called_once_with(self.USERNAME, self.course.org, opt_in)
        else:
            self.assertFalse(mock_update_email_opt_in.called)

    def test_user_not_authenticated(self):
        # Log out, so we're no longer authenticated
        self.client.logout()

        # Try to enroll, expecting a forbidden response
        resp = self._change_enrollment('enroll')
        self.assertEqual(resp.status_code, 403)

    def test_missing_course_id_param(self):
        resp = self.client.post(
            reverse('change_enrollment'),
            {'enrollment_action': 'enroll'}
        )
        self.assertEqual(resp.status_code, 400)

    def test_unenroll_not_enrolled_in_course(self):
        # Try unenroll without first enrolling in the course
        resp = self._change_enrollment('unenroll')
        self.assertEqual(resp.status_code, 400)

    def test_invalid_enrollment_action(self):
        resp = self._change_enrollment('not_an_action')
        self.assertEqual(resp.status_code, 400)

    def test_with_invalid_course_id(self):
        CourseEnrollment.enroll(self.user, self.course.id, mode="honor")
        resp = self._change_enrollment('unenroll', course_id="edx/")
        self.assertEqual(resp.status_code, 400)

    def _change_enrollment(self, action, course_id=None, email_opt_in=None):
        """Change the student's enrollment status in a course.

        Args:
            action (string): The action to perform (either "enroll" or "unenroll")

        Keyword Args:
            course_id (unicode): If provided, use this course ID.  Otherwise, use the
                course ID created in the setup for this test.
            email_opt_in (unicode): If provided, pass this value along as
                an additional GET parameter.

        Returns:
            Response

        """
        if course_id is None:
            course_id = unicode(self.course.id)

        params = {
            'enrollment_action': action,
            'course_id': course_id
        }

        if email_opt_in:
            params['email_opt_in'] = email_opt_in

        return self.client.post(reverse('change_enrollment'), params)
