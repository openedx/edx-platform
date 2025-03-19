"""
Tests for course dates views.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from edx_when.models import ContentDate, DatePolicy
from milestones.tests.utils import MilestonesTestCaseMixin
from rest_framework.test import APIRequestFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from lms.djangoapps.mobile_api.course_dates.views import AllCourseDatesViewSet
from lms.djangoapps.mobile_api.testutils import MobileAPITestCase
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase

User = get_user_model()


class TestAllCourseDatesViewSet(
    MobileAPITestCase, MixedSplitTestCase, MilestonesTestCaseMixin
):  # lint-amnesty, pylint: disable=test-inherits-tests
    """
    Tests for AllCourseDatesViewSet.
    """
    def setUp(self):
        """
        Set up the test cases.
        """
        super().setUp()

        self.course_1 = CourseFactory.create(modulestore=self.store)
        self.course_without_enrollment = CourseFactory.create(modulestore=self.store)

        self.course_overview_1 = CourseOverviewFactory.create(id=self.course_1.id, display_name="Test Course 1")
        self.course_overview_without_enrollment = CourseOverviewFactory.create(
            id=self.course_without_enrollment.id, display_name="Test Course Without Enrollment"
        )

        self.chapter_1 = self.make_block("chapter", self.course_1)
        self.sequential_1 = self.make_block("sequential", self.chapter_1)

        self.chapter_without_enrollment = self.make_block("chapter", self.course_without_enrollment)
        self.sequential_without_enrollment = self.make_block("sequential", self.chapter_without_enrollment)

        self.enrollment_1 = CourseEnrollmentFactory(user=self.user, course_id=self.course_1.id, is_active=True)

        self.date_policy_1 = DatePolicy.objects.create(abs_date=timezone.now() + timedelta(days=1))

        self.content_date_1 = ContentDate.objects.create(
            course_id=self.course_1.id,
            location=self.sequential_1.location,
            active=True,
            block_type="sequential",
            field="due",
            policy=self.date_policy_1,
        )
        self.content_date_without_enrollment = ContentDate.objects.create(
            course_id=self.course_without_enrollment.id,
            location=self.sequential_without_enrollment.location,
            active=True,
            block_type="sequential",
            field="due",
            policy=self.date_policy_1,
        )

    def _get_view_with_request(self):
        """
        Returns an instance of the view with a request.
        """
        request = APIRequestFactory().get(f"/api/mobile/v1/course_dates/{self.user.username}/")
        view = AllCourseDatesViewSet()
        view.request = request
        view.kwargs = {"username": self.user.username}
        return view

    def test_get_queryset(self):
        """
        Simple test to check if the queryset is returning the correct course dates.
        Dates from not enrolled courses should not be returned.
        """
        view = self._get_view_with_request()

        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.content_date_1)

    def test_get_queryset_with_relative_date(self):
        """
        Test to check if the queryset is returning the correct course dates with relative date.
        Due date should be calculated based on the enrollment date plus the relative date interval.
        """
        date_policy_with_relative_date = DatePolicy.objects.create(rel_date=timedelta(weeks=2))

        chapter_2 = self.make_block("chapter", self.course_1)
        sequential_2 = self.make_block("sequential", chapter_2)

        content_date_with_relative_date = ContentDate.objects.create(
            course_id=self.course_1.id,
            location=sequential_2.location,
            active=True,
            block_type="sequential",
            field="due",
            policy=date_policy_with_relative_date,
        )

        view = self._get_view_with_request()
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.content_date_1, queryset)
        self.assertIn(content_date_with_relative_date, queryset)

        content_date = queryset.filter(location=sequential_2.location).first()
        self.assertEqual(content_date.due_date, self.enrollment_1.created + date_policy_with_relative_date.rel_date)
        self.assertEqual(content_date.relative, True)

    def test_get_queryset_with_past_due_date_not_self_paced_course(self):
        """
        Test to check if not self paced courses with past due dates are not returned.
        """
        date_policy_past_due_date = DatePolicy.objects.create(abs_date=timezone.now() - timedelta(days=1))

        chapter_2 = self.make_block("chapter", self.course_1)
        sequential_2 = self.make_block("sequential", chapter_2)

        ContentDate.objects.create(
            course_id=self.course_1.id,
            location=sequential_2.location,
            active=True,
            block_type="sequential",
            field="due",
            policy=date_policy_past_due_date,
        )

        view = self._get_view_with_request()
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.content_date_1)

    def test_get_queryset_with_past_due_date_self_paced_course_with_relative_date(self):
        """
        Test to check if self paced courses with past due dates are returned.
        """
        self_paced_course = CourseFactory.create(modulestore=self.store)
        CourseOverviewFactory.create(id=self_paced_course.id, display_name="Self-paced Course", self_paced=True)
        CourseEnrollmentFactory(user=self.user, course_id=self_paced_course.id, is_active=True)
        chapter_2 = self.make_block("chapter", self_paced_course)
        sequential_2 = self.make_block("sequential", chapter_2)

        date_policy_past_due_date = DatePolicy.objects.create(rel_date=timedelta(weeks=-2))
        content_date_past_due_date = ContentDate.objects.create(
            course_id=self_paced_course.id,
            location=sequential_2.location,
            active=True,
            block_type="sequential",
            field="due",
            policy=date_policy_past_due_date,
        )

        view = self._get_view_with_request()
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.content_date_1, queryset)
        self.assertIn(content_date_past_due_date, queryset)
