"""
Tests for Progress Tab API in the Course Home API
"""

import dateutil
import ddt
from datetime import datetime, timedelta  # lint-amnesty, pylint: disable=wrong-import-order
from pytz import UTC
from unittest.mock import patch  # lint-amnesty, pylint: disable=wrong-import-order
from django.urls import reverse
from django.utils.timezone import now
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from lms.djangoapps.course_home_api.models import DisableProgressPageStackedConfig
from lms.djangoapps.course_home_api.toggles import COURSE_HOME_MICROFRONTEND_PROGRESS_TAB
from lms.djangoapps.verify_student.models import ManualVerification
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_date_signals.utils import MIN_DURATION
from openedx.features.content_type_gating.helpers import CONTENT_GATING_PARTITION_ID, CONTENT_TYPE_GATE_GROUP_IDS
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from xmodule.modulestore.tests.factories import ItemFactory  # lint-amnesty, pylint: disable=wrong-import-order


@ddt.ddt
class ProgressTabTestViews(BaseCourseHomeTests):
    """
    Tests for the Progress Tab API
    """
    def setUp(self):
        super().setUp()
        self.url = reverse('course-home:progress-tab', args=[self.course.id])

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_get_authenticated_enrolled_user(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        assert response.status_code == 200

        assert response.data['section_scores'] is not None
        for chapter in response.data['section_scores']:
            assert chapter is not None
        assert 'settings/grading/' + str(self.course.id) in response.data['studio_url']
        assert response.data['verification_data'] is not None
        assert response.data['verification_data']['status'] == 'none'
        if enrollment_mode == CourseMode.VERIFIED:
            ManualVerification.objects.create(user=self.user, status='approved')
            response = self.client.get(self.url)
            assert response.data['verification_data']['status'] == 'approved'
            assert response.data['certificate_data'] is None
        elif enrollment_mode == CourseMode.AUDIT:
            assert response.data['certificate_data']['cert_status'] == 'audit_passing'

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    @ddt.data(True, False)
    def test_get_authenticated_user_not_enrolled(self, has_previously_enrolled):
        if has_previously_enrolled:
            # Create an enrollment, then unenroll to set is_active to False
            CourseEnrollment.enroll(self.user, self.course.id)
            CourseEnrollment.unenroll(self.user, self.course.id)
        response = self.client.get(self.url)
        assert response.status_code == 401

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        assert response.status_code == 401

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_get_unknown_course(self):
        url = reverse('course-home:progress-tab', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        assert response.status_code == 404

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=False)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_waffle_flag_disabled(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        assert response.status_code == 404

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
    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_has_scheduled_content_data(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        future = now() + timedelta(days=30)
        ItemFactory(parent=self.course, category='chapter', start=future)
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.json()['has_scheduled_content']

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

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_user_has_passing_grade(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        self.course.grade_cutoffs = {'Pass': 0}
        self.update_course(self.course, self.user.id)
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.json()['user_has_passing_grade']

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_verified_mode(self):
        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['verified_mode'] == {'access_expiration_date': (enrollment.created + MIN_DURATION),
                                                  'currency': 'USD', 'currency_symbol': '$', 'price': 149,
                                                  'sku': 'ABCD1234', 'upgrade_url': '/dashboard'}

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_page_respects_stacked_config(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        course_overview = CourseOverview.get_from_id(self.course.id)

        response = self.client.get(self.url)
        assert response.status_code == 200

        DisableProgressPageStackedConfig.objects.create(disabled=True, course=course_overview)

        response = self.client.get(self.url)
        assert response.status_code == 404

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_learner_has_access(self):
        chapter = ItemFactory(parent=self.course, category='chapter')
        gated = ItemFactory(parent=chapter, category='sequential')
        ItemFactory.create(parent=gated, category='problem', graded=True, has_score=True)
        ungated = ItemFactory(parent=chapter, category='sequential')
        ItemFactory.create(parent=ungated, category='problem', graded=True, has_score=True,
                           group_access={
                               CONTENT_GATING_PARTITION_ID: [CONTENT_TYPE_GATE_GROUP_IDS['full_access'],
                                                             CONTENT_TYPE_GATE_GROUP_IDS['limited_access']],
                           })

        CourseEnrollment.enroll(self.user, self.course.id)
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        response = self.client.get(self.url)
        assert response.status_code == 200

        sections = response.data['section_scores']
        ungraded_score = sections[0]['subsections'][0]  # default sequence that parent class gives us
        gated_score = sections[1]['subsections'][0]
        ungated_score = sections[1]['subsections'][1]
        assert ungraded_score['learner_has_access']
        assert not gated_score['learner_has_access']
        assert ungated_score['learner_has_access']

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_view_other_students_progress_page(self):
        # Test the ability to view progress pages of other students by changing the url
        CourseEnrollment.enroll(self.user, self.course.id)
        response = self.client.get(self.url)
        assert response.data['username'] == self.user.username

        other_user = UserFactory()
        self.url = reverse('course-home:progress-tab-other-student', args=[self.course.id, other_user.id])
        CourseEnrollment.enroll(other_user, self.course.id)

        # users with the ccx coach role can view other students' progress pages
        with patch(
            'lms.djangoapps.course_home_api.progress.views.has_ccx_coach_role',
            return_value=True
        ):
            response = self.client.get(self.url)
            assert response.data['username'] == other_user.username

        # staff users can view other students' progress pages
        self.switch_to_staff()

        response = self.client.get(self.url)
        assert response.data['username'] == other_user.username

    @override_waffle_flag(COURSE_HOME_MICROFRONTEND_PROGRESS_TAB, active=True)
    def test_url_hidden_if_subsection_hide_after_due(self):
        chapter = ItemFactory(parent=self.course, category='chapter')
        yesterday = now() - timedelta(days=1)
        hide_after_due_subsection = ItemFactory(
            parent=chapter, category='sequential', hide_after_due=True, due=yesterday
        )

        CourseEnrollment.enroll(self.user, self.course.id)

        response = self.client.get(self.url)
        assert response.status_code == 200

        sections = response.data['section_scores']
        regular_subsection = sections[0]['subsections'][0]  # default sequence that parent class gives us
        hide_after_due_subsection = sections[1]['subsections'][0]
        assert regular_subsection['url'] is not None
        assert hide_after_due_subsection['url'] is None
