"""
Tests for Progress Tab API in the Course Home API
"""

import ddt
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from lms.djangoapps.course_home_api.toggles import COURSE_HOME_MICROFRONTEND, COURSE_HOME_MICROFRONTEND_PROGRESS_TAB
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from lms.djangoapps.verify_student.models import ManualVerification
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference

CREDIT_SUPPORT_URL = 'https://support.edx.org/hc/en-us/sections/115004154688-Purchasing-Academic-Credit'


@override_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
@ddt.ddt
class ProgressTabTestViews(BaseCourseHomeTests):
    """
    Tests for the Progress Tab API
    """
    def setUp(self):
        super().setUp()
        self.url = reverse('course-home-progress-tab', args=[self.course.id])

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_get_authenticated_enrolled_user(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        assert response.status_code == 200

        assert response.data['section_scores'] is not None
        for chapter in response.data['section_scores']:
            assert chapter is not None
        assert ('settings/grading/' + str(self.course.id)) in response.data['studio_url']
        assert response.data['verification_data'] is not None
        assert response.data['verification_data']['status'] == 'none'
        if enrollment_mode == CourseMode.VERIFIED:
            ManualVerification.objects.create(user=self.user, status='approved')
            response = self.client.get(self.url)
            assert response.data['verification_data']['status'] == 'approved'
            assert response.data['certificate_data'] is None
        elif enrollment_mode == CourseMode.AUDIT:
            assert response.data['certificate_data']['cert_status'] == 'audit_passing'

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_get_authenticated_user_not_enrolled(self):
        response = self.client.get(self.url)
        # expecting a redirect
        assert response.status_code == 302

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        assert response.status_code == 401

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_get_unknown_course(self):
        url = reverse('course-home-progress-tab', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        assert response.status_code == 404

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=False)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_waffle_flag_disabled(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        assert response.status_code == 404

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_masquerade(self):
        # Enroll a verified user
        verified_user = UserFactory(is_staff=False)
        CourseEnrollment.enroll(verified_user, self.course.id, CourseMode.VERIFIED)

        # Enroll self in course
        CourseEnrollment.enroll(self.user, self.course.id)
        response = self.client.get(self.url)
        assert response.status_code == 200

        self.switch_to_staff()  # needed for masquerade
        assert self.client.get(self.url).data.get('enrollment_mode') is None

        # Masquerade as verified user
        self.update_masquerade(username=verified_user.username)
        assert self.client.get(self.url).data.get('enrollment_mode') == 'verified'
