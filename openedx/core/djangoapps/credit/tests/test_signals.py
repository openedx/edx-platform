"""
Tests for minimum grade requirement status
"""

import pytz
import ddt
from datetime import timedelta, datetime

from django.test.client import RequestFactory

from openedx.core.djangoapps.credit.api import (
    set_credit_requirements, get_credit_requirement_status
)

from openedx.core.djangoapps.credit.models import CreditCourse, CreditProvider
from openedx.core.djangoapps.credit.signals import listen_for_grade_calculation
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class TestMinGradedRequirementStatus(ModuleStoreTestCase):
    """Test cases to check the minimum grade requirement status updated.
    If user grade is above or equal to min-grade then status will be
    satisfied. But if student grade is less than and deadline is passed then
    user will be marked as failed.
    """
    VALID_DUE_DATE = datetime.now(pytz.UTC) + timedelta(days=20)
    EXPIRED_DUE_DATE = datetime.now(pytz.UTC) - timedelta(days=20)

    def setUp(self):
        super(TestMinGradedRequirementStatus, self).setUp()
        self.course = CourseFactory.create(
            org='Robot', number='999', display_name='Test Course'
        )

        self.user = UserFactory()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.client.login(username=self.user.username, password=self.user.password)

        # Enable the course for credit
        CreditCourse.objects.create(
            course_key=self.course.id,
            enabled=True,
        )

        # Configure a credit provider for the course
        CreditProvider.objects.create(
            provider_id="ASU",
            enable_integration=True,
            provider_url="https://credit.example.com/request",
        )

        requirements = [{
            "namespace": "grade",
            "name": "grade",
            "display_name": "Grade",
            "criteria": {"min_grade": 0.52},
        }]
        # Add a single credit requirement (final grade)
        set_credit_requirements(self.course.id, requirements)

    @ddt.data(
        (0.6, VALID_DUE_DATE),
        (0.52, VALID_DUE_DATE),
        (0.70, EXPIRED_DUE_DATE),
    )
    @ddt.unpack
    def test_min_grade_requirement_with_valid_grade(self, grade_achieved, due_date):
        """Test with valid grades. Deadline date does not effect in case
        of valid grade.
        """

        listen_for_grade_calculation(None, self.user.username, {'percent': grade_achieved}, self.course.id, due_date)
        req_status = get_credit_requirement_status(self.course.id, self.request.user.username, 'grade', 'grade')
        self.assertEqual(req_status[0]["status"], 'satisfied')

    @ddt.data(
        (0.50, None),
        (0.51, None),
        (0.40, VALID_DUE_DATE),
    )
    @ddt.unpack
    def test_min_grade_requirement_failed_grade_valid_deadline(self, grade_achieved, due_date):
        """Test with failed grades and deadline is still open or not defined."""

        listen_for_grade_calculation(None, self.user.username, {'percent': grade_achieved}, self.course.id, due_date)
        req_status = get_credit_requirement_status(self.course.id, self.request.user.username, 'grade', 'grade')
        self.assertEqual(req_status[0]["status"], None)

    def test_min_grade_requirement_failed_grade_expired_deadline(self):
        """Test with failed grades and deadline expire"""

        listen_for_grade_calculation(None, self.user.username, {'percent': 0.22}, self.course.id, self.EXPIRED_DUE_DATE)
        req_status = get_credit_requirement_status(self.course.id, self.request.user.username, 'grade', 'grade')
        self.assertEqual(req_status[0]["status"], 'failed')
