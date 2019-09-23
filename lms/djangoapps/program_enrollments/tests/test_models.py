"""
Unit tests for ProgramEnrollment models.
"""
from __future__ import absolute_import, unicode_literals

from uuid import uuid4

import ddt
import mock
from django.db.utils import IntegrityError
from django.test import TestCase
from edx_django_utils.cache import RequestCache
from opaque_keys.edx.keys import CourseKey
from testfixtures import LogCapture

from course_modes.models import CourseMode
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from openedx.core.djangoapps.catalog.tests.factories import generate_course_run_key
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.models import CourseEnrollment, NonExistentCourseError
from student.tests.factories import CourseEnrollmentFactory, UserFactory


class ProgramEnrollmentModelTests(TestCase):
    """
    Tests for the ProgramEnrollment model.
    """
    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(ProgramEnrollmentModelTests, self).setUp()
        self.user = UserFactory.create()
        self.program_uuid = uuid4()
        self.other_program_uuid = uuid4()
        self.curriculum_uuid = uuid4()
        self.enrollment = ProgramEnrollment.objects.create(
            user=self.user,
            external_user_key='abc',
            program_uuid=self.program_uuid,
            curriculum_uuid=self.curriculum_uuid,
            status='enrolled'
        )

    def test_unique_external_key_program_curriculum(self):
        """
        A record with the same (external_user_key, program_uuid, curriculum_uuid) cannot be duplicated.
        """
        with self.assertRaises(IntegrityError):
            _ = ProgramEnrollment.objects.create(
                user=None,
                external_user_key='abc',
                program_uuid=self.program_uuid,
                curriculum_uuid=self.curriculum_uuid,
                status='pending',
            )

    def test_unique_user_program_curriculum(self):
        """
        A record with the same (user, program_uuid, curriculum_uuid) cannot be duplicated.
        """
        with self.assertRaises(IntegrityError):
            _ = ProgramEnrollment.objects.create(
                user=self.user,
                external_user_key=None,
                program_uuid=self.program_uuid,
                curriculum_uuid=self.curriculum_uuid,
                status='suspended',
            )

    def test_user_retirement(self):
        """
        Test that the external_user_key is successfully retired for a user's program enrollments
        and history.
        """
        new_status = 'canceled'

        self.enrollment.status = new_status
        self.enrollment.save()

        # Ensure that all the records had values for external_user_key
        self.assertEquals(self.enrollment.external_user_key, 'abc')

        self.assertTrue(self.enrollment.historical_records.all())
        for record in self.enrollment.historical_records.all():
            self.assertEquals(record.external_user_key, 'abc')

        ProgramEnrollment.retire_user(self.user.id)
        self.enrollment.refresh_from_db()

        # Ensure those values are retired
        self.assertEquals(self.enrollment.external_user_key, None)

        self.assertTrue(self.enrollment.historical_records.all())
        for record in self.enrollment.historical_records.all():
            self.assertEquals(record.external_user_key, None)


@ddt.ddt
class ProgramCourseEnrollmentModelTests(TestCase):
    """
    Tests for the ProgramCourseEnrollment model.
    """
    def setUp(self):
        """
        Set up test data
        """
        super(ProgramCourseEnrollmentModelTests, self).setUp()
        RequestCache.clear_all_namespaces()
        self.user = UserFactory.create()
        self.program_uuid = uuid4()
        self.program_enrollment = ProgramEnrollment.objects.create(
            user=self.user,
            external_user_key='abc',
            program_uuid=self.program_uuid,
            curriculum_uuid=uuid4(),
            status='enrolled'
        )
        self.course_key = CourseKey.from_string(generate_course_run_key())
        CourseOverviewFactory(id=self.course_key)

    def test_unique_completed_enrollment(self):
        """
        A record with the same (program_enrollment, course_enrollment)
        cannot be created.
        """
        pce = self._create_completed_program_course_enrollment()
        with self.assertRaises(IntegrityError):
            # Purposefully mis-set the course_key in order to test
            # that there is a constraint on
            # (program_enrollment, course_enrollment) alone.
            ProgramCourseEnrollment.objects.create(
                program_enrollment=pce.program_enrollment,
                course_key="course-v1:dummy+value+101",
                course_enrollment=pce.course_enrollment,
                status="inactive",
            )

    def test_unique_waiting_enrollment(self):
        """
        A record with the same (program_enrollment, course_key)
        cannot be created.
        """
        pce = self._create_waiting_program_course_enrollment()
        with self.assertRaises(IntegrityError):
            ProgramCourseEnrollment.objects.create(
                program_enrollment=pce.program_enrollment,
                course_key=pce.course_key,
                course_enrollment=None,
                status="inactive",
            )

    def _create_completed_program_course_enrollment(self):
        """ helper function create program course enrollment """
        course_enrollment = CourseEnrollmentFactory.create(
            course_id=self.course_key,
            user=self.user,
            mode=CourseMode.MASTERS
        )
        program_course_enrollment = ProgramCourseEnrollment.objects.create(
            program_enrollment=self.program_enrollment,
            course_key=self.course_key,
            course_enrollment=course_enrollment,
            status="active"
        )
        return program_course_enrollment

    def _create_waiting_program_course_enrollment(self):
        """ helper function create program course enrollment with no lms user """
        return ProgramCourseEnrollment.objects.create(
            program_enrollment=self.program_enrollment,
            course_key=self.course_key,
            course_enrollment=None,
            status="active"
        )

    def test_change_status_no_enrollment(self):
        program_course_enrollment = self._create_completed_program_course_enrollment()
        with LogCapture() as capture:
            program_course_enrollment.course_enrollment = None
            program_course_enrollment.change_status("inactive")
            expected_message = "User {} {} {} has no course_enrollment".format(
                self.user,
                self.program_enrollment,
                self.course_key
            )
            capture.check(
                ('lms.djangoapps.program_enrollments.models', 'WARNING', expected_message)
            )

    def test_change_status_not_active_or_inactive(self):
        program_course_enrollment = self._create_completed_program_course_enrollment()
        with LogCapture() as capture:
            status = "potential-future-status-0123"
            program_course_enrollment.change_status(status)
            message = ("Changed {} status to {}, not changing course_enrollment"
                       " status because status is not 'active' or 'inactive'")
            expected_message = message.format(program_course_enrollment, status)
            capture.check(
                ('lms.djangoapps.program_enrollments.models', 'WARNING', expected_message)
            )

    def test_enroll_new_course_enrollment(self):
        program_course_enrollment = self._create_waiting_program_course_enrollment()
        program_course_enrollment.enroll(self.user)

        course_enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_key)
        self.assertEqual(course_enrollment.user, self.user)
        self.assertEqual(course_enrollment.course.id, self.course_key)
        self.assertEqual(course_enrollment.mode, CourseMode.MASTERS)

    def test_enrollment_course_not_found(self):
        nonexistent_key = 'course-v1:edX+Overview+DNE'
        program_course_enrollment = ProgramCourseEnrollment.objects.create(
            program_enrollment=self.program_enrollment,
            course_key=nonexistent_key,
            course_enrollment=None,
            status="active"
        )

        with LogCapture() as capture:
            with self.assertRaises(NonExistentCourseError):
                program_course_enrollment.enroll(self.user)
            expected = "User {} failed to enroll in non-existent course {}".format(
                self.user.id, nonexistent_key
            )
            capture.check(
                ('lms.djangoapps.program_enrollments.models', 'WARNING', expected)
            )

    @ddt.data(
        (CourseMode.VERIFIED, CourseMode.VERIFIED),
        (CourseMode.AUDIT, CourseMode.MASTERS),
        (CourseMode.HONOR, CourseMode.MASTERS)
    )
    @ddt.unpack
    def test_enroll_existing_course_enrollment(self, original_mode, result_mode):
        course_enrollment = CourseEnrollmentFactory.create(
            course_id=self.course_key,
            user=self.user,
            mode=original_mode
        )
        program_course_enrollment = self._create_waiting_program_course_enrollment()

        program_course_enrollment.enroll(self.user)

        course_enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_key)
        self.assertEqual(course_enrollment.user, self.user)
        self.assertEqual(course_enrollment.course.id, self.course_key)
        self.assertEqual(course_enrollment.mode, result_mode)

    @mock.patch('student.models.CourseEnrollment.is_enrollment_closed', return_value=True)
    def test_closed_enrollments_ignored(self, _mock):
        """ enrolling through program enrollments should ignore checks on enrollment """
        program_course_enrollment = self._create_waiting_program_course_enrollment()
        program_course_enrollment.enroll(self.user)

        course_enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_key)
        self.assertEqual(course_enrollment.user, self.user)
        self.assertEqual(course_enrollment.course.id, self.course_key)
        self.assertEqual(course_enrollment.mode, CourseMode.MASTERS)
