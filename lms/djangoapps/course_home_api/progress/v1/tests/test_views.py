"""
Tests for Progress Tab API in the Course Home API
"""

import dateutil
import ddt
import mock
from datetime import datetime, timedelta
from pytz import UTC
from unittest.mock import patch
from django.urls import reverse
from django.utils.timezone import now
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from lms.djangoapps.course_home_api.toggles import COURSE_HOME_MICROFRONTEND, COURSE_HOME_MICROFRONTEND_PROGRESS_TAB
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from lms.djangoapps.verify_student.models import ManualVerification
from openedx.core.djangoapps.course_date_signals.utils import MIN_DURATION
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from xmodule.modulestore.tests.factories import ItemFactory

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
    @ddt.data(True, False)
    def test_get_authenticated_user_not_enrolled(self, has_previously_enrolled):
        if has_previously_enrolled:
            # Create an enrollment, then unenroll to set is_active to False
            CourseEnrollment.enroll(self.user, self.course.id)
            CourseEnrollment.unenroll(self.user, self.course.id)
        response = self.client.get(self.url)
        assert response.status_code == 401

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

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_has_scheduled_content_data(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        future = now() + timedelta(days=30)
        chapter = ItemFactory(parent=self.course, category='chapter', start=future)
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.json()['has_scheduled_content']

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_end(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        future = now() + timedelta(days=30)
        self.course.end = future
        self.update_course(self.course, self.user.id)
        response = self.client.get(self.url)
        assert response.status_code == 200
        end = dateutil.parser.parse(response.json()['end']).replace(tzinfo=UTC)
        assert end.date() == future.date()

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_user_has_passing_grade(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        self.course._grading_policy['GRADE_CUTOFFS']['Pass'] = 0
        self.update_course(self.course, self.user.id)
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.json()['user_has_passing_grade']

    @override_experiment_waffle_flag(COURSE_HOME_MICROFRONTEND, active=True)
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_verified_mode(self):
        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['verified_mode'] == {'access_expiration_date': (enrollment.created + MIN_DURATION),
                                                  'currency': 'USD', 'currency_symbol': '$', 'price': 149,
                                                  'sku': 'ABCD1234', 'upgrade_url': '/dashboard'}
