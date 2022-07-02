"""
Unit tests for program_course_enrollments tasks
"""


from datetime import timedelta

import pytest
from django.db.models.base import ObjectDoesNotExist
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from opaque_keys.edx.keys import CourseKey
from testfixtures import LogCapture

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from lms.djangoapps.program_enrollments.tasks import expire_waiting_enrollments, log
from lms.djangoapps.program_enrollments.tests.factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


class ExpireWaitingEnrollmentsTest(TestCase):
    """ Test expire_waiting_enrollments task """

    @classmethod
    def setUpClass(cls):
        super(cls, ExpireWaitingEnrollmentsTest).setUpClass()
        cls.timed_course_key = CourseKey.from_string('course-v1:edX+TestExpire+Timed')
        cls.fresh_course_key = CourseKey.from_string('course-v1:edX+TestExpire+Fresh')
        CourseOverviewFactory(id=cls.timed_course_key)
        CourseOverviewFactory(id=cls.fresh_course_key)

    def _set_up_course_enrollment(self, user, program_enrollment, course_key):
        """ helper function to set up a program course enrollment """
        if user:
            ProgramCourseEnrollmentFactory(
                program_enrollment=program_enrollment,
                course_enrollment=CourseEnrollmentFactory(
                    course_id=course_key, user=user, mode=CourseMode.MASTERS
                )
            )
        else:
            ProgramCourseEnrollmentFactory(
                program_enrollment=program_enrollment,
                course_key=course_key,
            )

    def _set_up_enrollments(self, external_user_key, user, created_date):
        """ helper function to setup enrollments """
        with freeze_time(created_date):
            program_enrollment = ProgramEnrollmentFactory(
                user=user,
                external_user_key=external_user_key,
            )
            self._set_up_course_enrollment(
                user, program_enrollment, self.timed_course_key
            )
        # additional course enrollment that is always fresh
        self._set_up_course_enrollment(
            user, program_enrollment, self.fresh_course_key
        )

    def test_expire(self):
        self._set_up_enrollments('student_expired_waiting', None, timezone.now() - timedelta(60))
        self._set_up_enrollments('student_waiting', None, timezone.now() - timedelta(59))
        self._set_up_enrollments('student_actualized', UserFactory(), timezone.now() - timedelta(90))

        expired_program_enrollment = ProgramEnrollment.objects.get(
            external_user_key='student_expired_waiting'
        )
        expired_course_enrollments = list(ProgramCourseEnrollment.objects.filter(
            program_enrollment=expired_program_enrollment
        ))

        # assert deleted enrollments are logged (without pii)
        with LogCapture(log.name) as log_capture:
            expire_waiting_enrollments(60)

            program_enrollment_message_tmpl = 'Found expired program_enrollment (id={}) for program_uuid={}'
            course_enrollment_message_tmpl = (
                'Found expired program_course_enrollment (id={}) for program_uuid={}, course_key={}'
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
            )

            assert 'Removed 3 expired records:' in log_capture.records[3].getMessage()
            assert "program_enrollments.ProgramCourseEnrollment': 2" in log_capture.records[3].getMessage()
            assert "program_enrollments.ProgramEnrollment': 1" in log_capture.records[3].getMessage()

        program_enrollments = ProgramEnrollment.objects.all()
        program_course_enrollments = ProgramCourseEnrollment.objects.all()
        historical_program_enrollments = ProgramEnrollment.historical_records.all()  # pylint: disable=no-member
        historical_program_course_enrollments = ProgramCourseEnrollment.historical_records.all()  # pylint: disable=no-member

        # assert expired records no longer exist
        with pytest.raises(ProgramEnrollment.DoesNotExist):
            program_enrollments.get(external_user_key='student_expired_waiting')
        assert len(program_course_enrollments) == 4

        # assert fresh waiting records are not affected
        waiting_enrollment = program_enrollments.get(external_user_key='student_waiting')
        assert len(waiting_enrollment.program_course_enrollments.all()) == 2

        # assert actualized enrollments are not affected
        actualized_enrollment = program_enrollments.get(external_user_key='student_actualized')
        assert len(actualized_enrollment.program_course_enrollments.all()) == 2

        # assert expired historical records are also removed
        with pytest.raises(ObjectDoesNotExist):
            historical_program_enrollments.get(external_user_key='student_expired_waiting')
        assert len(historical_program_course_enrollments
                   .filter(program_enrollment_id=expired_program_enrollment.id)) == 0

        # assert other historical records are not affected
        assert len(historical_program_enrollments) == 2
        assert len(historical_program_course_enrollments) == 4

    def test_expire_none(self):
        """ Asserts no exceptions are thrown if no enrollments are found """
        expire_waiting_enrollments(60)
        assert len(ProgramEnrollment.objects.all()) == 0
