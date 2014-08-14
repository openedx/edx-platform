import ddt
import unittest
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch, Mock

from course_modes.tests.factories import CourseModeFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey


@ddt.ddt
class CourseModeViewTest(TestCase):

    def setUp(self):
        self.course_id = SlashSeparatedCourseKey('org', 'course', 'run')

        for mode in ('audit', 'verified', 'honor'):
            CourseModeFactory(mode_slug=mode, course_id=self.course_id)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @ddt.data(
        # is_active?, enrollment_mode, upgrade?, redirect?
        (True, 'verified', True, True),     # User is already verified
        (True, 'verified', False, True),    # User is already verified
        (True, 'honor', True, False),       # User isn't trying to upgrade
        (True, 'honor', False, True),       # User is trying to upgrade
        (True, 'audit', True, False),       # User isn't trying to upgrade
        (True, 'audit', False, True),       # User is trying to upgrade
        (False, 'verified', True, False),   # User isn't active
        (False, 'verified', False, False),  # User isn't active
        (False, 'honor', True, False),      # User isn't active
        (False, 'honor', False, False),     # User isn't active
        (False, 'audit', True, False),      # User isn't active
        (False, 'audit', False, False),     # User isn't active
    )
    @ddt.unpack
    @patch('course_modes.views.modulestore', Mock())
    def test_reregister_redirect(self, is_active, enrollment_mode, upgrade, redirect):
        enrollment = CourseEnrollmentFactory(
            is_active=is_active,
            mode=enrollment_mode,
            course_id=self.course_id
        )

        self.client.login(
            username=enrollment.user.username,
            password='test'
        )

        if upgrade:
            get_params = {'upgrade': True}
        else:
            get_params = {}

        response = self.client.get(
            reverse('course_modes_choose', args=[self.course_id.to_deprecated_string()]),
            get_params,
            follow=False,
        )

        if redirect:
            self.assertEquals(response.status_code, 302)
            self.assertTrue(response['Location'].endswith(reverse('dashboard')))
        else:
            self.assertEquals(response.status_code, 200)
            # TODO: Fix it so that response.templates works w/ mako templates, and then assert
            # that the right template rendered

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @ddt.data(
        '',
        '1,,2',
        '1, ,2',
        '1, 2, 3'
    )
    @patch('course_modes.views.modulestore', Mock())
    def test_suggested_prices(self, price_list):
        course_id = SlashSeparatedCourseKey('org', 'course', 'price_course')
        user = UserFactory()

        for mode in ('audit', 'honor'):
            CourseModeFactory(mode_slug=mode, course_id=course_id)

        CourseModeFactory(mode_slug='verified', course_id=course_id, suggested_prices=price_list)

        self.client.login(
            username=user.username,
            password='test'
        )

        response = self.client.get(
            reverse('course_modes_choose', args=[self.course_id.to_deprecated_string()]),
            follow=False,
        )

        self.assertEquals(response.status_code, 200)
        # TODO: Fix it so that response.templates works w/ mako templates, and then assert
        # that the right template rendered


class ProfessionalModeViewTest(TestCase):
    """
    Tests for redirects specific to the 'professional' course mode.
    Can't really put this in the ddt-style tests in CourseModeViewTest,
    since 'professional' mode implies it is the *only* mode for a course
    """
    def setUp(self):
        self.course_id = SlashSeparatedCourseKey('org', 'course', 'run')
        CourseModeFactory(mode_slug='professional', course_id=self.course_id)
        self.user = UserFactory()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_professional_registration(self):
        self.client.login(
            username=self.user.username,
            password='test'
        )

        response = self.client.get(
            reverse('course_modes_choose', args=[self.course_id.to_deprecated_string()]),
            follow=False,
        )

        self.assertEquals(response.status_code, 302)
        self.assertTrue(response['Location'].endswith(reverse('verify_student_show_requirements', args=[unicode(self.course_id)])))

        CourseEnrollmentFactory(
            user=self.user,
            is_active=True,
            mode="professional",
            course_id=unicode(self.course_id),
        )

        response = self.client.get(
            reverse('course_modes_choose', args=[self.course_id.to_deprecated_string()]),
            follow=False,
        )

        self.assertEquals(response.status_code, 302)
        self.assertTrue(response['Location'].endswith(reverse('dashboard')))
