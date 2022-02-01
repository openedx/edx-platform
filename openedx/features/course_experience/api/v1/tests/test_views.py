"""
Tests for reset deadlines endpoint.
"""
import datetime
import ddt

from django.urls import reverse
from django.utils import timezone

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.testing import EventTestMixin
from lms.djangoapps.courseware.tests.helpers import MasqueradeMixin
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from openedx.core.djangoapps.schedules.models import Schedule
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


@ddt.ddt
class ResetCourseDeadlinesViewTests(EventTestMixin, BaseCourseHomeTests, MasqueradeMixin):
    """
    Tests for reset deadlines endpoint.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        # Need to supply tracker name for the EventTestMixin. Also, EventTestMixin needs to come
        # first in class inheritance so the setUp call here appropriately works
        super().setUp('openedx.features.course_experience.api.v1.views.tracker')

    def test_reset_deadlines(self):
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.VERIFIED)
        # Test body with incorrect body param (course_key is required)
        response = self.client.post(reverse('course-experience-reset-course-deadlines'), {'course': self.course.id})
        assert response.status_code == 400
        self.assert_no_events_were_emitted()

        # Test correct post body
        response = self.client.post(reverse('course-experience-reset-course-deadlines'), {'course_key': self.course.id})
        assert response.status_code == 200
        self.assert_event_emitted(
            'edx.ui.lms.reset_deadlines.clicked',
            courserun_key=str(self.course.id),
            is_masquerading=False,
            is_staff=False,
            org_key=self.course.org,
            user_id=self.user.id,
        )

    def test_reset_deadlines_with_masquerade(self):
        """ Staff users should be able to masquerade as a learner and reset the learner's schedule """
        course = CourseFactory.create(self_paced=True, start=timezone.now() - datetime.timedelta(days=1))
        student_username = self.user.username
        student_user_id = self.user.id
        student_enrollment = CourseEnrollment.enroll(self.user, course.id)
        student_enrollment.schedule.start_date = timezone.now() - datetime.timedelta(days=100)
        student_enrollment.schedule.save()

        staff_enrollment = CourseEnrollment.enroll(self.staff_user, course.id)
        staff_enrollment.schedule.start_date = timezone.now() - datetime.timedelta(days=30)
        staff_enrollment.schedule.save()

        self.switch_to_staff()
        self.update_masquerade(course=course, username=student_username)

        self.client.post(reverse('course-experience-reset-course-deadlines'), {'course_key': course.id})
        updated_schedule = Schedule.objects.get(id=student_enrollment.schedule.id)
        assert updated_schedule.start_date.date() == datetime.datetime.today().date()
        updated_staff_schedule = Schedule.objects.get(id=staff_enrollment.schedule.id)
        assert updated_staff_schedule.start_date == staff_enrollment.schedule.start_date
        self.assert_event_emitted(
            'edx.ui.lms.reset_deadlines.clicked',
            courserun_key=str(course.id),
            is_masquerading=True,
            is_staff=False,
            org_key=course.org,
            user_id=student_user_id,
        )

    def test_post_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(reverse('course-experience-reset-course-deadlines'), {'course_key': self.course.id})
        assert response.status_code == 401

    def test_mobile_get_banner_info(self):
        response = self.client.get(reverse('course-experience-course-deadlines-mobile', args=[self.course.id]))
        assert response.status_code == 200
        self.assertContains(response, 'missed_deadlines')
        self.assertContains(response, 'missed_gated_content')
        self.assertContains(response, 'content_type_gating_enabled')
        self.assertContains(response, 'verified_upgrade_link')

    def test_mobile_get_unknown_course(self):
        url = reverse('course-experience-course-deadlines-mobile', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        assert response.status_code == 404

    def test_mobile_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(reverse('course-experience-course-deadlines-mobile', args=[self.course.id]))
        assert response.status_code == 401
