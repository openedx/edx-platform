"""
Test that various filters are fired for models/views in the student app.
"""
from django.test import override_settings
from django.urls import reverse
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import CourseEnrollmentStarted, CourseUnenrollmentStarted
from rest_framework import status
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.models import CourseEnrollment, EnrollmentNotAllowed, UnenrollmentNotAllowed
from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


class TestEnrollmentPipelineStep(PipelineStep):
    """
    Utility function used when getting steps for pipeline.
    """

    def run_filter(self, user, course_key, mode):  # pylint: disable=arguments-differ
        """Pipeline steps that changes mode to honor."""
        if mode == "no-id-professional":
            raise CourseEnrollmentStarted.PreventEnrollment()
        return {"mode": "honor"}


class TestUnenrollmentPipelineStep(PipelineStep):
    """
    Utility function used when getting steps for pipeline.
    """

    def run_filter(self, enrollment):  # pylint: disable=arguments-differ
        """Pipeline steps that modifies user's profile before unenrolling."""
        if enrollment.mode == "no-id-professional":
            raise CourseUnenrollmentStarted.PreventUnenrollment(
                "You can't un-enroll from this site."
            )

        enrollment.user.profile.set_meta({"unenrolled_from": str(enrollment.course_id)})
        enrollment.user.profile.save()
        return {}


@skip_unless_lms
class EnrollmentFiltersTest(ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the enrollment process through the enroll method.

    This class guarantees that the following filters are triggered during the user's enrollment:

    - CourseEnrollmentStarted
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(
            username="test",
            email="test@example.com",
            password="password",
        )
        self.user_profile = UserProfileFactory.create(user=self.user, name="Test Example")

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course.enrollment.started.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestEnrollmentPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_enrollment_filter_executed(self):
        """
        Test whether the student enrollment filter is triggered before the user's
        enrollment process.

        Expected result:
            - CourseEnrollmentStarted is triggered and executes TestEnrollmentPipelineStep.
            - The arguments that the receiver gets are the arguments used by the filter
            with the enrollment mode changed.
        """
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='audit')

        self.assertEqual('honor', enrollment.mode)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course.enrollment.started.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestEnrollmentPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_enrollment_filter_prevent_enroll(self):
        """
        Test prevent the user's enrollment through a pipeline step.

        Expected result:
            - CourseEnrollmentStarted is triggered and executes TestEnrollmentPipelineStep.
            - The user can't enroll.
        """
        with self.assertRaises(EnrollmentNotAllowed):
            CourseEnrollment.enroll(self.user, self.course.id, mode='no-id-professional')

    @override_settings(OPEN_EDX_FILTERS_CONFIG={})
    def test_enrollment_without_filter_configuration(self):
        """
        Test usual enrollment process, without filter's intervention.

        Expected result:
            - CourseEnrollmentStarted does not have any effect on the enrollment process.
            - The enrollment process ends successfully.
        """
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='audit')

        self.assertEqual('audit', enrollment.mode)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))


@skip_unless_lms
class UnenrollmentFiltersTest(ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the unenrollment process through the unenroll method.

    This class guarantees that the following filters are triggered during the user's unenrollment:

    - CourseUnenrollmentStarted
    """

    USERNAME = "test"
    EMAIL = "test@example.com"
    PASSWORD = "password"

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course.unenrollment.started.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestUnenrollmentPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_unenrollment_filter_executed(self):
        """
        Test whether the student unenrollment filter is triggered before the user's
        unenrollment process.

        Expected result:
            - CourseUnenrollmentStarted is triggered and executes TestUnenrollmentPipelineStep.
            - The user's profile has unenrolled_from in its meta field.
        """
        CourseEnrollment.enroll(self.user, self.course.id, mode="audit")

        CourseEnrollment.unenroll(self.user, self.course.id)

        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course.unenrollment.started.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestUnenrollmentPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_unenrollment_filter_prevent_unenroll(self):
        """
        Test prevent the user's unenrollment through a pipeline step.

        Expected result:
            - CourseUnenrollmentStarted is triggered and executes TestUnenrollmentPipelineStep.
            - The user can't unenroll.
        """
        CourseEnrollment.enroll(self.user, self.course.id, mode="no-id-professional")

        with self.assertRaises(UnenrollmentNotAllowed):
            CourseEnrollment.unenroll(self.user, self.course.id)

    @override_settings(OPEN_EDX_FILTERS_CONFIG={})
    def test_unenrollment_without_filter_configuration(self):
        """
        Test usual unenrollment process without filter's intervention.

        Expected result:
            - CourseUnenrollmentStarted does not have any effect on the unenrollment process.
            - The unenrollment process ends successfully.
        """
        CourseEnrollment.enroll(self.user, self.course.id, mode="audit")

        CourseEnrollment.unenroll(self.user, self.course.id)

        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course.unenrollment.started.v1": {
                "pipeline": [
                    "common.djangoapps.student.tests.test_filters.TestUnenrollmentPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_unenrollment_blocked_by_filter(self):
        """
        Test cannot unenroll using change_enrollment view course when UnenrollmentNotAllowed is
        raised by unenroll method.

        Expected result:
            - CourseUnenrollmentStarted does not have any effect on the unenrollment process.
            - The unenrollment process ends successfully.
        """
        CourseEnrollment.enroll(self.user, self.course.id, mode="no-id-professional")
        params = {
            "enrollment_action": "unenroll",
            "course_id": str(self.course.id)
        }

        response = self.client.post(reverse("change_enrollment"), params)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual("You can't un-enroll from this site.", response.content.decode("utf-8"))
