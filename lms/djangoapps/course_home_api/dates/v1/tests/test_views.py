"""
Tests for Dates Tab API in the Course Home API
"""

from datetime import datetime

import ddt
from django.urls import reverse

from common.djangoapps.course_modes.models import CourseMode
from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from lms.djangoapps.course_home_api.toggles import COURSE_HOME_MICROFRONTEND, COURSE_HOME_MICROFRONTEND_DATES_TAB
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from common.djangoapps.student.models import CourseEnrollment


@ddt.ddt
class DatesTabTestViews(BaseCourseHomeTests):
    """
    Tests for the Dates Tab API
    """
    def setUp(self):
        super().setUp()
        self.url = reverse('course-home-dates-tab', args=[self.course.id])
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2017, 1, 1))

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_DATES_TAB, active=True)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_get_authenticated_enrolled_user(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Pulling out the date blocks to check learner has access.
        date_blocks = response.data.get('course_date_blocks')
        self.assertEqual(response.data.get('learner_is_full_access'), enrollment_mode == CourseMode.VERIFIED)
        self.assertTrue(all(block.get('learner_has_access') for block in date_blocks))

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_DATES_TAB, active=True)
    def test_get_authenticated_user_not_enrolled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data.get('learner_is_full_access'))

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_DATES_TAB, active=True)
    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_DATES_TAB, active=True)
    def test_get_unknown_course(self):
        url = reverse('course-home-dates-tab', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_DATES_TAB, active=True)
    def test_banner_data_is_returned(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'missed_deadlines')
        self.assertContains(response, 'missed_gated_content')
        self.assertContains(response, 'content_type_gating_enabled')
        self.assertContains(response, 'verified_upgrade_link')

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_DATES_TAB, active=True)
    def test_masquerade(self):
        self.switch_to_staff()
        CourseEnrollment.enroll(self.user, self.course.id, 'audit')
        self.assertTrue(self.client.get(self.url).data.get('learner_is_full_access'))

        self.update_masquerade(role='student')
        self.assertFalse(self.client.get(self.url).data.get('learner_is_full_access'))
