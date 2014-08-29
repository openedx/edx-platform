"""
Tests for student enrollment.
"""
from datetime import datetime, timedelta
import pytz
import ddt
import unittest

from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
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

    # TODO (ECOM-16): We need separate test cases for both conditions in the auto-registration
    # AB-test.  Once we get the results of that test, we should
    # remove the losing condition from this test.
    @ddt.data(
        # Default (no course modes in the database)
        # Expect that we're redirected to the dashboard
        # and automatically enrolled as "honor"
        ([], '', 'honor', False),
        ([], '', 'honor', True),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page,
        # If auto-registration is enabled, we should also be registered
        # as "honor" by default.
        (['honor', 'verified', 'audit'], 'course_modes_choose', None, False),
        (['honor', 'verified', 'audit'], 'course_modes_choose', 'honor', True),

        # Professional ed
        # Expect that we're sent to the "choose your track" page
        # (which will, in turn, redirect us to a page where we can verify/pay)
        # Even if auto registration is enabled, we should NOT be auto-registered,
        # because that would be giving away an expensive course for free :)
        (['professional'], 'course_modes_choose', None, False),
        (['professional'], 'course_modes_choose', None, True),

    )
    @ddt.unpack
    def test_enroll(self, course_modes, next_url, enrollment_mode, auto_reg):
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
        resp = self._change_enrollment('enroll', auto_reg=auto_reg)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, full_url)

        # TODO (ECOM-16): If auto-registration is enabled, check that we're
        # storing the auto-reg flag in the user's session
        if auto_reg:
            self.assertIn('auto_register', self.client.session)
            self.assertTrue(self.client.session['auto_register'])

        # If we're not expecting to be enrolled, verify that this is the case
        if enrollment_mode is None:
            self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

        # Otherwise, verify that we're enrolled with the expected course mode
        else:
            self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
            course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
            self.assertTrue(is_active)
            self.assertEqual(course_mode, enrollment_mode)

    # TODO (ECOM-16): Remove once the auto-registration A/B test completes.
    def test_enroll_from_redirect_autoreg(self):
        # Bugfix (ECOM-199): Visitors removed from auto-enroll pool
        # if they need to authenticate while attempting to enroll.
        # If a user is (a) in the experimental condition of the A/B test (autoreg enabled)
        # and (b) is not logged in when registering for a course, then
        # the user will be redirected to the "control" URL (change_enrollment)
        # instead of the experimental URL (change_enrollment_autoreg)
        # We work around this by setting a flag in the session, such that
        # if a user is *ever* in the experimental condition, they remain
        # in the experimental condition.
        for mode_slug in ['honor', 'audit', 'verified']:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode_slug,
                mode_display_name=mode_slug
            )

        # Log out, so we're no longer authenticated
        self.client.logout()

        # Visit the experimental condition URL
        resp = self._change_enrollment('enroll', auto_reg=True)

        # Expect that we're denied (since we're not authenticated)
        # and instead are redirected to the login page
        self.assertEqual(resp.status_code, 403)

        # Log the user in
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

        # Go to the control URL
        # This simulates what the JavaScript client does after getting a 403 response
        # from the register button.
        resp = self._change_enrollment('enroll')

        # Expect that we're auto-enrolled (even though we used the control URL the second time)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))

        # Expect that the auto register flag is still set in the user's session
        self.assertIn('auto_register', self.client.session)
        self.assertTrue(self.client.session['auto_register'])

    # TODO (ECOM-16): Remove once the auto-registration A/B test completes
    def test_enroll_auto_registration_excluded_course(self):
        # Create the course modes
        for mode_slug in ['honor', 'audit', 'verified']:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode_slug,
                mode_display_name=mode_slug,
            )

        # Visit the experimental condition URL (when the course is NOT excluded)
        # This should place us into the experimental condition flow
        self._change_enrollment('enroll', auto_reg=True)

        # Unenroll from the course (we were registered because auto enroll was enabled)
        self._change_enrollment('unenroll')

        # Register for the course again, with the course excluded
        # At this point, we should NOT be in the experimental condition flow
        excluded_course_ids = [self.course.id.to_deprecated_string()]
        with self.settings(AUTO_REGISTRATION_AB_TEST_EXCLUDE_COURSES=excluded_course_ids):
            self._change_enrollment('enroll')
            self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))
            self.assertNotIn('auto_register', self.client.session)

    def test_unenroll(self):
        # Enroll the student in the course
        CourseEnrollment.enroll(self.user, self.course.id, mode="honor")

        # Attempt to unenroll the student
        resp = self._change_enrollment('unenroll')
        self.assertEqual(resp.status_code, 200)

        # Expect that we're no longer enrolled
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

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

    def _change_enrollment(self, action, course_id=None, auto_reg=False):
        """
        Change the student's enrollment status in a course.

        Args:
            action (string): The action to perform (either "enroll" or "unenroll")

        Keyword Args:
            course_id (unicode): If provided, use this course ID.  Otherwise, use the
                course ID created in the setup for this test.

            auto_reg (boolean): Whether to use the auto-registration hook.
                TODO (ECOM-16): remove this once we complete the AB test for auto-registration.

        Returns:
            Response

        """
        if course_id is None:
            course_id = unicode(self.course.id)

        url = (
            reverse('change_enrollment')
            if not auto_reg
            else reverse('change_enrollment_autoreg')
        )
        params = {
            'enrollment_action': action,
            'course_id': course_id
        }
        return self.client.post(url, params)
