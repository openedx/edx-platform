"""
Tests for student enrollment.
"""
import ddt
import unittest
from mock import patch
from nose.plugins.attrib import attr

from django.conf import settings
from django.core.urlresolvers import reverse
from course_modes.models import CourseMode
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from util.testing import UrlResetMixin
from embargo.test_utils import restrict_course
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment, CourseFullError
from student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
)


@attr('shard_3')
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentTest(UrlResetMixin, SharedModuleStoreTestCase):
    """
    Test student enrollment, especially with different course modes.
    """

    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"
    URLCONF_MODULES = ['embargo']

    @classmethod
    def setUpClass(cls):
        super(EnrollmentTest, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_limited = CourseFactory.create()

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        """ Create a course and user, then log in. """
        super(EnrollmentTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.course_limited.max_student_enrollments_allowed = 1
        self.store.update_item(self.course_limited, self.user.id)
        self.urls = [
            reverse('course_modes_choose', kwargs={'course_id': unicode(self.course.id)})
        ]

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that we're redirected to the dashboard
        # and automatically enrolled
        ([], '', CourseMode.DEFAULT_MODE_SLUG),

        # Audit / Verified
        # We should always go to the "choose your course" page.
        # We should also be enrolled as the default mode.
        (['verified', 'audit'], 'course_modes_choose', CourseMode.DEFAULT_MODE_SLUG),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as the honor mode.
        # Since honor and audit are currently offered together this precedence must
        # be maintained.
        (['honor', 'verified', 'audit'], 'course_modes_choose', CourseMode.HONOR),

        # Professional ed
        # Expect that we're sent to the "choose your track" page
        # (which will, in turn, redirect us to a page where we can verify/pay)
        # We should NOT be auto-enrolled, because that would be giving
        # away an expensive course for free :)
        (['professional'], 'course_modes_choose', None),
        (['no-id-professional'], 'course_modes_choose', None),
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

    def test_unenroll(self):
        # Enroll the student in the course
        CourseEnrollment.enroll(self.user, self.course.id, mode="honor")

        # Attempt to unenroll the student
        resp = self._change_enrollment('unenroll')
        self.assertEqual(resp.status_code, 200)

        # Expect that we're no longer enrolled
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_EMAIL_OPT_IN': True})
    @patch('openedx.core.djangoapps.user_api.preferences.api.update_email_opt_in')
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
        (['no-id-professional'], 'true'),
        (['no-id-professional'], 'false'),
        (['no-id-professional'], None),
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
            mock_update_email_opt_in.assert_called_once_with(self.user, self.course.org, opt_in)
        else:
            self.assertFalse(mock_update_email_opt_in.called)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_restrict(self):
        # When accessing the course from an embargoed country,
        # we should be blocked.
        with restrict_course(self.course.id) as redirect_url:
            response = self._change_enrollment('enroll')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, redirect_url)

        # Verify that we weren't enrolled
        is_enrolled = CourseEnrollment.is_enrolled(self.user, self.course.id)
        self.assertFalse(is_enrolled)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_allow(self):
        response = self._change_enrollment('enroll')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '')

        # Verify that we were enrolled
        is_enrolled = CourseEnrollment.is_enrolled(self.user, self.course.id)
        self.assertTrue(is_enrolled)

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

    def test_enrollment_limit(self):
        """
        Assert that in a course with max student limit set to 1, we can enroll staff and instructor along with
        student. To make sure course full check excludes staff and instructors.
        """
        self.assertEqual(self.course_limited.max_student_enrollments_allowed, 1)
        user1 = UserFactory.create(username="tester1", email="tester1@e.com", password="test")
        user2 = UserFactory.create(username="tester2", email="tester2@e.com", password="test")

        # create staff on course.
        staff = UserFactory.create(username="staff", email="staff@e.com", password="test")
        role = CourseStaffRole(self.course_limited.id)
        role.add_users(staff)

        # create instructor on course.
        instructor = UserFactory.create(username="instructor", email="instructor@e.com", password="test")
        role = CourseInstructorRole(self.course_limited.id)
        role.add_users(instructor)

        CourseEnrollment.enroll(staff, self.course_limited.id, check_access=True)
        CourseEnrollment.enroll(instructor, self.course_limited.id, check_access=True)

        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=self.course_limited.id, user=staff).exists()
        )

        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=self.course_limited.id, user=instructor).exists()
        )

        CourseEnrollment.enroll(user1, self.course_limited.id, check_access=True)
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=self.course_limited.id, user=user1).exists()
        )

        with self.assertRaises(CourseFullError):
            CourseEnrollment.enroll(user2, self.course_limited.id, check_access=True)

        self.assertFalse(
            CourseEnrollment.objects.filter(course_id=self.course_limited.id, user=user2).exists()
        )

    def _change_enrollment(self, action, course_id=None, email_opt_in=None):
        """Change the student's enrollment status in a course.

        Args:
            action (str): The action to perform (either "enroll" or "unenroll")

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
