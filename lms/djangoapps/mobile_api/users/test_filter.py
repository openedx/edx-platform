"""
Test that various filters are fired for models/views in the student app.
"""
from django.test import override_settings
from unittest.mock import MagicMock

from lms.djangoapps.mobile_api.users.views import UserCourseEnrollmentsList
from common.djangoapps.student.models import CourseEnrollment
from openedx_filters import PipelineStep
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.mobile_api.utils import API_V1
from lms.djangoapps.mobile_api.testutils import MobileAPITestCase
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


class TestCourseEnrollmentsPipelineStep(PipelineStep):
    """
    Utility function used when getting steps for pipeline.
    """

    def run_filter(self, enrollments):  # pylint: disable=arguments-differ
        """Pipeline steps that modifies course enrollments when make a queryset request."""

        enrollments = [enrollment for enrollment in enrollments if enrollment.course.org == "demo"]
        return enrollments


@skip_unless_lms
class EnrollmentFiltersTest(MobileAPITestCase, ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the enrollment process through the enroll method.

    This class guarantees that the following filters are triggered during the user's enrollment:

    - CourseEnrollmentQuerysetRequested
    """
    REVERSE_INFO = {'name': 'user-info', 'params': ['api_version']}

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.user = UserFactory.create(
            username="test",
            email="test@example.com",
            password="password",
        )
        demo_course = CourseFactory.create(org='demo', mobile_available=True)
        test_course = CourseFactory.create(org='test', mobile_available=True)
        CourseEnrollment.enroll(self.user, demo_course.id)
        CourseEnrollment.enroll(self.user, test_course.id)
        self.mock_request = MagicMock()
        self.mock_request.query_params.get.return_value = ''
        view = UserCourseEnrollmentsList(
            kwargs={"username": self.user.username, "api_version": API_V1}
        )
        view.request = self.mock_request
        self.enrollment = view.get_queryset()

    @override_settings()
    def test_enrollment_queryset_filter_unexecuted_views(self):
        """
        Test filter enrollment queryset when a request is made.

        Expected result:
            - CourseEnrollmentQuerysetRequested is triggered and executes TestCourseEnrollmentsPipelineStep.
            - The result is a list of course enrollments queryset filter by org
        """
        view = UserCourseEnrollmentsList(
            kwargs={"username": self.user.username, "api_version": API_V1}
        )
        view.request = self.mock_request
        enrollments = view.get_queryset()

        self.assertEqual(self.enrollment, enrollments)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course_enrollment_queryset.requested.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestCourseEnrollmentsPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_enrollment_queryset_filter_executed_views(self):
        """
        Test filter enrollment queryset when a request is made.

        Expected result:
            - CourseEnrollmentQuerysetRequested is triggered and executes TestCourseEnrollmentsPipelineStep.
            - The result is a list of course enrollments queryset filter by org
        """
        expected_enrollment = self.enrollment

        view = UserCourseEnrollmentsList(
            kwargs={"username": self.user.username, "api_version": API_V1}
        )
        view.request = self.mock_request
        enrollments = view.get_queryset()

        self.assertAlmostEqual(len(enrollments), len(expected_enrollment), 1)
        self.assertEqual(expected_enrollment.course.org, "helo")
