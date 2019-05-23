"""
Unit tests for program_course_enrollments tasks
"""
from datetime import timedelta
from django.db.models.base import ObjectDoesNotExist
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from testfixtures import LogCapture
from lms.djangoapps.program_enrollments.models import ProgramEnrollment, ProgramCourseEnrollment
from lms.djangoapps.program_enrollments.tasks import expire_waiting_enrollments, log
from lms.djangoapps.program_enrollments.api.v1.tests.factories import (
    ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
)
from student.tests.factories import UserFactory


class ExpireWaitingEnrollmentsTest(TestCase):
    """ Test expire_waiting_enrollments task """

    def _setup_enrollments(self, external_user_key, user, created_date):
        """ helper function to setup enrollments """
        with freeze_time(created_date):
            program_enrollment = ProgramEnrollmentFactory(
                user=user,
                external_user_key=external_user_key,
            )
            ProgramCourseEnrollmentFactory(
                program_enrollment=program_enrollment
            )
        # additional course enrollment that is always fresh
        ProgramCourseEnrollmentFactory(
            program_enrollment=program_enrollment
        )

    def test_expire(self):
        self._setup_enrollments('student_expired_waiting', None, timezone.now() - timedelta(60))
        self._setup_enrollments('student_waiting', None, timezone.now() - timedelta(59))
        self._setup_enrollments('student_actualized', UserFactory(), timezone.now() - timedelta(90))

        expired_program_enrollment = ProgramEnrollment.objects.get(
            external_user_key='student_expired_waiting'
        )
        expired_course_enrollments = list(ProgramCourseEnrollment.objects.filter(
            program_enrollment=expired_program_enrollment
        ))

        # assert deleted enrollments are logged (without pii)
        with LogCapture(log.name) as log_capture:
            expire_waiting_enrollments(60)

            program_enrollment_message_tmpl = u'Found expired program_enrollment (id={}) for program_uuid={}'
            course_enrollment_message_tmpl = (
                u'Found expired program_course_enrollment (id={}) for program_uuid={}, course_key={}'
            )

            log_capture.check_present(
                (
                    log.name,
                    'INFO',
                    program_enrollment_message_tmpl.format(
                        expired_program_enrollment.id,
                        expired_program_enrollment.program_uuid,
                    )
                ),
                (
                    log.name,
                    'INFO',
                    course_enrollment_message_tmpl.format(
                        expired_course_enrollments[0].id,
                        expired_program_enrollment.program_uuid,
                        expired_course_enrollments[0].course_key,
                    )
                ),
                (
                    log.name,
                    'INFO',
                    course_enrollment_message_tmpl.format(
                        expired_course_enrollments[1].id,
                        expired_program_enrollment.program_uuid,
                        expired_course_enrollments[1].course_key,
                    )
                ),
                (
                    log.name,
                    'INFO',
                    u'Removed 3 expired records:'
                    u' {u\'program_enrollments.ProgramCourseEnrollment\': 2,'
                    u' u\'program_enrollments.ProgramEnrollment\': 1}'
                ),
            )

        program_enrollments = ProgramEnrollment.objects.all()
        program_course_enrollments = ProgramCourseEnrollment.objects.all()
        historical_program_enrollments = ProgramEnrollment.historical_records.all()  # pylint: disable=no-member
        historical_program_course_enrollments = ProgramCourseEnrollment.historical_records.all()  # pylint: disable=no-member

        # assert expired records no longer exist
        with self.assertRaises(ProgramEnrollment.DoesNotExist):
            program_enrollments.get(external_user_key='student_expired_waiting')
        self.assertEqual(len(program_course_enrollments), 4)

        # assert fresh waiting records are not affected
        waiting_enrollment = program_enrollments.get(external_user_key='student_waiting')
        self.assertEqual(len(waiting_enrollment.program_course_enrollments.all()), 2)

        # assert actualized enrollments are not affected
        actualized_enrollment = program_enrollments.get(external_user_key='student_actualized')
        self.assertEqual(len(actualized_enrollment.program_course_enrollments.all()), 2)

        # assert expired historical records are also removed
        with self.assertRaises(ObjectDoesNotExist):
            historical_program_enrollments.get(external_user_key='student_expired_waiting')
        self.assertEqual(
            len(historical_program_course_enrollments.filter(program_enrollment_id=expired_program_enrollment.id)),
            0
        )

        # assert other historical records are not affected
        self.assertEqual(len(historical_program_enrollments), 2)
        self.assertEqual(len(historical_program_course_enrollments), 4)

    def test_expire_none(self):
        """ Asserts no exceptions are thrown if no enrollments are found """
        expire_waiting_enrollments(60)
        self.assertEqual(len(ProgramEnrollment.objects.all()), 0)
