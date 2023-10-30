"""
Test for the NotificationFilter class.
"""
from datetime import timedelta
from unittest import mock

import ddt
from django.utils.timezone import now

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.notifications.filters import NotificationFilter
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from openedx.features.course_experience.tests.views.helpers import add_course_mode
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class CourseExpirationTestCase(ModuleStoreTestCase):
    """Tests to verify the get_user_course_expiration_date function is working correctly"""

    def setUp(self):
        super().setUp()  # lint-amnesty, pylint: disable=super-with-arguments
        self.course = CourseFactory(
            start=now() - timedelta(weeks=10),
        )

        self.user = UserFactory()
        self.user_1 = UserFactory()

        # Make this a verified course, so we can test expiration date
        add_course_mode(self.course, mode_slug=CourseMode.AUDIT)
        add_course_mode(self.course)
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)
        expired_audit = CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)
        expired_audit.created = now() - timedelta(weeks=6)
        expired_audit.save()

    @mock.patch("openedx.core.djangoapps.course_date_signals.utils.get_course_run_details")
    def test_audit_expired_filter(
        self,
        mock_get_course_run_details,
    ):
        """
        Test if filter_audit_expired function is working correctly
        """

        mock_get_course_run_details.return_value = {'weeks_to_complete': 4}
        result = NotificationFilter.filter_audit_expired(
            [self.user.id, self.user_1.id],
            self.course,
        )
        self.assertEqual([self.user_1.id], result)

        mock_get_course_run_details.return_value = {'weeks_to_complete': 7}
        result = NotificationFilter.filter_audit_expired(
            [self.user.id, self.user_1.id],
            self.course,
        )
        self.assertEqual([self.user.id, self.user_1.id], result)

        CourseDurationLimitConfig.objects.create(
            enabled=True,
            course=CourseOverview.get_from_id(self.course.id),
            enabled_as_of=now(),
        )
        # weeks_to_complete is set to 4 because we want to test if CourseDurationLimitConfig is working correctly.
        mock_get_course_run_details.return_value = {'weeks_to_complete': 4}
        result = NotificationFilter.filter_audit_expired(
            [self.user.id, self.user_1.id],
            self.course,
        )
        self.assertEqual([self.user.id, self.user_1.id], result)

    @mock.patch("openedx.core.djangoapps.course_date_signals.utils.get_course_run_details")
    @mock.patch("openedx.core.djangoapps.notifications.filters.NotificationFilter.filter_audit_expired")
    def test_apply_filter(
        self,
        mock_filter_audit_expired,
        mock_get_course_run_details,
    ):
        """
        Test if apply_filter function is working correctly
        """
        mock_get_course_run_details.return_value = {'weeks_to_complete': 4}
        mock_filter_audit_expired.return_value = [self.user.id, self.user_1.id]
        result = NotificationFilter().apply_filters(
            [self.user.id, self.user_1.id],
            self.course.id,
            'new_comment_on_response'
        )
        self.assertEqual([self.user.id, self.user_1.id], result)
        mock_filter_audit_expired.assert_called_once()
