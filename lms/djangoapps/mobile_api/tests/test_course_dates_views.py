"""
Tests for course dates views.
"""

from datetime import timedelta
from dateutil import parser

from django.contrib.auth import get_user_model
from django.utils import timezone
from edx_when.models import ContentDate, DatePolicy, UserDate
from milestones.tests.utils import MilestonesTestCaseMixin

from lms.djangoapps.mobile_api.testutils import MobileAPITestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase

User = get_user_model()


class TestAllCourseDatesAPIView(
    MobileAPITestCase, MixedSplitTestCase, MilestonesTestCaseMixin
):  # lint-amnesty, pylint: disable=test-inherits-tests
    """
    Tests for AllCourseDatesAPIView.
    """

    REVERSE_INFO = {'name': 'all-course-dates', 'params': ['api_version', 'username']}

    def setUp(self):
        """
        Set up the test cases.
        """
        super().setUp()
        self.course_1 = CourseFactory.create(modulestore=self.store)
        self.chapter_1 = self.make_block("chapter", self.course_1)
        self.sequential_1 = self.make_block("sequential", self.chapter_1)
        self.date_policy_1 = DatePolicy.objects.create(abs_date=timezone.now() + timedelta(days=1))
        self.content_date_1 = ContentDate.objects.create(
            course_id=self.course_1.id,
            location=self.sequential_1.location,
            active=True,
            block_type="sequential",
            field="due",
            policy=self.date_policy_1,
        )

    def tearDown(self):
        UserDate.objects.all().delete()
        super().tearDown()

    def test_only_future_dates_are_returned(self):
        """
        Ensure GET only returns user dates strictly after now().
        We create 3 UserDates: 1 in the past, 1 in the present, 1 in the future.
        We expect to get back 1 UserDate - the one from the future.
        """
        now = timezone.now()
        # past date (should be excluded)
        UserDate.objects.create(user=self.user, content_date=self.content_date_1, abs_date=now - timedelta(days=1))
        # today (should be excluded)
        UserDate.objects.create(user=self.user, content_date=self.content_date_1, abs_date=now)
        # future date (should be included)
        future_date = UserDate.objects.create(user=self.user, content_date=self.content_date_1,
                                              abs_date=now + timedelta(days=2))

        self.login_and_enroll(self.course_1.id)
        response = self.api_response()

        results = response.data["results"]
        self.assertEqual(len(results), 1)
        returned_date = parser.parse(results[0]["due_date"]).replace(microsecond=0)
        expected_date = future_date.actual_date.replace(microsecond=0)
        self.assertEqual(returned_date, expected_date)

    def test_results_are_sorted_by_actual_date(self):
        """
        Ensure results come in ascending order by actual_date.
        """
        now = timezone.now()
        # Three future dates, intentionally unsorted
        d3 = UserDate.objects.create(user=self.user, content_date=self.content_date_1, abs_date=now + timedelta(days=3))
        d1 = UserDate.objects.create(user=self.user, content_date=self.content_date_1, abs_date=now + timedelta(days=1))
        d2 = UserDate.objects.create(user=self.user, content_date=self.content_date_1, abs_date=now + timedelta(days=2))

        self.login_and_enroll(self.course_1.id)
        response = self.api_response(username=self.user.username)

        results = response.data["results"]
        returned_dates = [parser.parse(result["due_date"]).replace(microsecond=0) for result in results]
        expected_dates = [d.replace(microsecond=0) for d in (d1.actual_date, d2.actual_date, d3.actual_date)]
        self.assertListEqual(returned_dates, expected_dates)

    def test_empty_results_if_no_future_dates(self):
        """
        Ensure GET returns empty list when all dates are in the past.
        """
        now = timezone.now()
        UserDate.objects.create(user=self.user, content_date=self.content_date_1, abs_date=now - timedelta(days=10))
        UserDate.objects.create(user=self.user, content_date=self.content_date_1, abs_date=now - timedelta(days=1))

        self.login_and_enroll(self.course_1.id)
        response = self.api_response(username=self.user.username)

        self.assertListEqual(response.data["results"], [])
