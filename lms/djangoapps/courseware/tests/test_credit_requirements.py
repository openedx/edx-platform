"""
Tests for credit requirement display on the progress page.
"""

import datetime

import ddt
from mock import patch
from pytz import UTC

from django.conf import settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from util.date_utils import get_time_display, DEFAULT_SHORT_DATE_FORMAT

from course_modes.models import CourseMode
from openedx.core.djangoapps.credit import api as credit_api
from openedx.core.djangoapps.credit.models import CreditCourse


@patch.dict(settings.FEATURES, {"ENABLE_CREDIT_ELIGIBILITY": True})
@ddt.ddt
class ProgressPageCreditRequirementsTest(SharedModuleStoreTestCase):
    """
    Tests for credit requirement display on the progress page.
    """

    USERNAME = "bob"
    PASSWORD = "test"
    USER_FULL_NAME = "Bob"

    MIN_GRADE_REQ_DISPLAY = "Final Grade Credit Requirement"
    VERIFICATION_REQ_DISPLAY = "Midterm Exam Credit Requirement"

    @classmethod
    def setUpClass(cls):
        super(ProgressPageCreditRequirementsTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(ProgressPageCreditRequirementsTest, self).setUp()

        # Configure course as a credit course
        CreditCourse.objects.create(course_key=self.course.id, enabled=True)

        # Configure credit requirements (passing grade and in-course reverification)
        credit_api.set_credit_requirements(
            self.course.id,
            [
                {
                    "namespace": "grade",
                    "name": "grade",
                    "display_name": self.MIN_GRADE_REQ_DISPLAY,
                    "criteria": {
                        "min_grade": 0.8
                    }
                },
                {
                    "namespace": "reverification",
                    "name": "midterm",
                    "display_name": self.VERIFICATION_REQ_DISPLAY,
                    "criteria": {}
                }
            ]
        )

        # Create a user and log in
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        self.user.profile.name = self.USER_FULL_NAME
        self.user.profile.save()

        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in")

        # Enroll the user in the course as "verified"
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            mode="verified"
        )

    def test_credit_requirements_maybe_eligible(self):
        # The user hasn't satisfied any of the credit requirements yet, but she
        # also hasn't failed any.
        response = self._get_progress_page()

        # Expect that the requirements are displayed
        self.assertContains(response, self.MIN_GRADE_REQ_DISPLAY)
        self.assertContains(response, self.VERIFICATION_REQ_DISPLAY)
        self.assertContains(response, "Upcoming")
        self.assertContains(
            response,
            "{}, you have not yet met the requirements for credit".format(self.USER_FULL_NAME)
        )

    def test_credit_requirements_eligible(self):
        # Mark the user as eligible for all requirements
        credit_api.set_credit_requirement_status(
            self.user.username, self.course.id,
            "grade", "grade",
            status="satisfied",
            reason={"final_grade": 0.95}
        )

        credit_api.set_credit_requirement_status(
            self.user.username, self.course.id,
            "reverification", "midterm",
            status="satisfied", reason={}
        )

        # Check the progress page display
        response = self._get_progress_page()
        self.assertContains(response, self.MIN_GRADE_REQ_DISPLAY)
        self.assertContains(response, self.VERIFICATION_REQ_DISPLAY)
        self.assertContains(
            response,
            "{}, you have met the requirements for credit in this course.".format(self.USER_FULL_NAME)
        )
        self.assertContains(response, "Completed by {date}".format(date=self._now_formatted_date()))
        self.assertNotContains(response, "95%")

    def test_credit_requirements_not_eligible(self):
        # Mark the user as having failed both requirements
        credit_api.set_credit_requirement_status(
            self.user.username, self.course.id,
            "reverification", "midterm",
            status="failed", reason={}
        )

        # Check the progress page display
        response = self._get_progress_page()
        self.assertContains(response, self.MIN_GRADE_REQ_DISPLAY)
        self.assertContains(response, self.VERIFICATION_REQ_DISPLAY)
        self.assertContains(
            response,
            "{}, you are no longer eligible for credit in this course.".format(self.USER_FULL_NAME)
        )
        self.assertContains(response, "Verification Failed")

    @ddt.data(
        (CourseMode.VERIFIED, True),
        (CourseMode.CREDIT_MODE, True),
        (CourseMode.HONOR, False),
        (CourseMode.AUDIT, False),
        (CourseMode.PROFESSIONAL, False),
        (CourseMode.NO_ID_PROFESSIONAL_MODE, False)
    )
    @ddt.unpack
    def test_credit_requirements_on_progress_page(self, enrollment_mode, is_requirement_displayed):
        """Test the progress table is only displayed to the verified and credit students."""
        self.enrollment.mode = enrollment_mode
        self.enrollment.save()  # pylint: disable=no-member

        response = self._get_progress_page()
        # Verify the requirements are shown only if the user is in a credit-eligible mode.
        classes = ('credit-eligibility', 'eligibility-heading')
        method = self.assertContains if is_requirement_displayed else self.assertNotContains

        for _class in classes:
            method(response, _class)

    def _get_progress_page(self):
        """Load the progress page for the course the user is enrolled in. """
        url = reverse("progress", kwargs={"course_id": unicode(self.course.id)})
        return self.client.get(url)

    def _now_formatted_date(self):
        """Retrieve the formatted current date. """
        return get_time_display(
            datetime.datetime.now(UTC),
            DEFAULT_SHORT_DATE_FORMAT,
            settings.TIME_ZONE
        )
