"""
Tests for the link_program_enrollments management command.
"""
from __future__ import absolute_import

from uuid import uuid4
from testfixtures import LogCapture

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from edx_django_utils.cache import RequestCache
from lms.djangoapps.program_enrollments.management.commands.link_program_enrollments import (
    Command,
    INCORRECT_PARAMETER_TPL,
    DUPLICATE_KEY_TPL,
    NO_PROGRAM_ENROLLMENT_TPL,
    NO_LMS_USER_TPL,
    COURSE_ENROLLMENT_ERR_TPL,
    get_existing_user_message,
)
from lms.djangoapps.program_enrollments.tests.factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.tests.factories import UserFactory

COMMAND_PATH = 'lms.djangoapps.program_enrollments.management.commands.link_program_enrollments'


class TestLinkProgramEnrollmentsMixin(object):
    """ Utility methods and test data for testing the link_program_enrollments command """

    @classmethod
    def setUpTestData(cls):  # pylint: disable=missing-docstring
        cls.command = Command()
        cls.program = uuid4()
        cls.other_program = uuid4()
        cls.fruit_course = CourseKey.from_string('course-v1:edX+Oranges+Apples')
        cls.animal_course = CourseKey.from_string('course-v1:edX+Cats+Dogs')
        CourseOverviewFactory.create(id=cls.fruit_course)
        CourseOverviewFactory.create(id=cls.animal_course)

    def setUp(self):
        self.user_1 = UserFactory.create()
        self.user_2 = UserFactory.create()

    def tearDown(self):
        RequestCache.clear_all_namespaces()

    def call_command(self, program_uuid, *user_info):
        """
        Builds string arguments and calls the link_program_enrollments command
        """
        command_args = [external_key + ":" + lms_username for external_key, lms_username in user_info]
        call_command(self.command, program_uuid, *command_args)

    def _create_waiting_enrollment(self, program_uuid, external_user_key):
        """
        Create a waiting program enrollment for the given program and external user key.
        """
        return ProgramEnrollmentFactory.create(
            user=None,
            program_uuid=program_uuid,
            external_user_key=external_user_key,
        )

    def _create_waiting_course_enrollment(self, program_enrollment, course_key, status='active'):
        """
        Create a waiting program course enrollment for the given program enrollment, course key, and optionally status
        """
        return ProgramCourseEnrollmentFactory.create(
            program_enrollment=program_enrollment,
            course_key=course_key,
            course_enrollment=None,
            status=status,
        )

    def _assert_no_user(self, program_enrollment, refresh=True):
        """
        Assert that the given program enrollment has no LMS user associated with it
        """
        if refresh:
            program_enrollment.refresh_from_db()
        self.assertIsNone(program_enrollment.user)

    def _assert_no_program_enrollment(self, user, program_uuid, refresh=True):
        """
        Assert that the given user is not enrolled in the given program
        """
        if refresh:
            user.refresh_from_db()
        self.assertFalse(user.programenrollment_set.filter(program_uuid=program_uuid).exists())

    def _assert_program_enrollment(self, user, program_uuid, external_user_key, refresh=True):
        """
        Assert that the given user is enrolled in the given program with the given external user key
        """
        if refresh:
            user.refresh_from_db()
        enrollment = user.programenrollment_set.get(program_uuid=program_uuid, external_user_key=external_user_key)
        self.assertIsNotNone(enrollment)

    def _assert_user_enrolled_in_program_courses(self, user, program_uuid, *course_keys):
        """
        Assert that the given user is has active enrollments in the given courses through the given program
        """
        user.refresh_from_db()
        program_enrollment = user.programenrollment_set.get(user=user, program_uuid=program_uuid)
        all_course_enrollments = program_enrollment.program_course_enrollments
        program_course_enrollments = all_course_enrollments.select_related(
            'course_enrollment__course'
        ).filter(
            course_enrollment__isnull=False
        )
        course_enrollments = [
            program_course_enrollment.course_enrollment
            for program_course_enrollment in program_course_enrollments
        ]
        self.assertTrue(all(course_enrollment.is_active for course_enrollment in course_enrollments))
        self.assertCountEqual(
            course_keys,
            [course_enrollment.course.id for course_enrollment in course_enrollments]
        )


class TestLinkProgramEnrollments(TestLinkProgramEnrollmentsMixin, TestCase):
    """ Tests for link_program_enrollments behavior """

    def test_link_only_specified_program(self):
        """
        Test that when there are two waiting program enrollments with the same external user key,
        only the specified program's program enrollment will be linked
        """
        program_enrollment = self._create_waiting_enrollment(self.program, '0001')
        self._create_waiting_course_enrollment(program_enrollment, self.fruit_course)
        self._create_waiting_course_enrollment(program_enrollment, self.animal_course)

        another_program_enrollment = self._create_waiting_enrollment(self.other_program, '0001')
        self._create_waiting_course_enrollment(another_program_enrollment, self.fruit_course)
        self._create_waiting_course_enrollment(another_program_enrollment, self.animal_course)

        self.call_command(self.program, ('0001', self.user_1.username))

        self._assert_program_enrollment(self.user_1, self.program, '0001')
        self._assert_user_enrolled_in_program_courses(self.user_1, self.program, self.fruit_course, self.animal_course)

        self._assert_no_user(another_program_enrollment)

    def test_inactive_waiting_course_enrollment(self):
        """
        Test that when a waiting program enrollment has waiting program course enrollments with a status of 'inactive'
        the course enrollment created after calling link_program_enrollments will be inactive
        """
        program_enrollment = self._create_waiting_enrollment(self.program, '0001')
        active_enrollment = self._create_waiting_course_enrollment(
            program_enrollment,
            self.fruit_course
        )
        inactive_enrollment = self._create_waiting_course_enrollment(
            program_enrollment,
            self.animal_course,
            status='inactive'
        )

        self.call_command(self.program, ('0001', self.user_1.username))

        self._assert_program_enrollment(self.user_1, self.program, '0001')

        active_enrollment.refresh_from_db()
        self.assertIsNotNone(active_enrollment.course_enrollment)
        self.assertEqual(active_enrollment.course_enrollment.course.id, self.fruit_course)
        self.assertTrue(active_enrollment.course_enrollment.is_active)

        inactive_enrollment.refresh_from_db()
        self.assertIsNotNone(inactive_enrollment.course_enrollment)
        self.assertEqual(inactive_enrollment.course_enrollment.course.id, self.animal_course)
        self.assertFalse(inactive_enrollment.course_enrollment.is_active)


class TestLinkProgramEnrollmentsErrors(TestLinkProgramEnrollmentsMixin, TestCase):
    """ Tests for link_program_enrollments error behavior """

    def test_incorrectly_formatted_input(self):
        with self.assertRaisesRegex(CommandError, INCORRECT_PARAMETER_TPL.format('whoops')):
            call_command(self.command, self.program, 'learner-01:user-01', 'whoops', 'learner-03:user-03')

    def test_repeated_user_key(self):
        with self.assertRaisesRegex(CommandError, DUPLICATE_KEY_TPL.format('learner-01')):
            self.call_command(self.program, ('learner-01', 'user-01'), ('learner-01', 'user-02'))

    def test_program_enrollment_not_found__nonexistant(self):
        self._create_waiting_enrollment(self.program, '0001')
        self._program_enrollment_not_found()

    def test_program_enrollment_not_found__different_program(self):
        self._create_waiting_enrollment(self.program, '0001')
        self._create_waiting_enrollment(self.other_program, '0002')
        self._program_enrollment_not_found()

    def _program_enrollment_not_found(self):
        """
        Helper for test_program_not_found_* tests.
        tries to link user_1 to '0001' and user_2 to '0002' in program
        asserts that user_2 was not linked because the enrollment was not found
        """
        with LogCapture() as logger:
            self.call_command(self.program, ('0001', self.user_1.username), ('0002', self.user_2.username))
            logger.check_present(
                (COMMAND_PATH, 'WARNING', NO_PROGRAM_ENROLLMENT_TPL.format(
                    program_uuid=self.program,
                    external_student_key='0002'
                ))
            )

        self._assert_program_enrollment(self.user_1, self.program, '0001')
        self._assert_no_program_enrollment(self.user_2, self.program)

    def test_user_not_found(self):
        self._create_waiting_enrollment(self.program, '0001')
        enrollment_2 = self._create_waiting_enrollment(self.program, '0002')

        with LogCapture() as logger:
            self.call_command(self.program, ('0001', self.user_1.username), ('0002', 'nonexistant-user'))
            logger.check_present(
                (COMMAND_PATH, 'WARNING', NO_LMS_USER_TPL.format('nonexistant-user'))
            )

        self._assert_program_enrollment(self.user_1, self.program, '0001')
        self._assert_no_user(enrollment_2)

    def test_enrollment_already_linked_to_target_user(self):
        self._create_waiting_enrollment(self.program, '0001')
        program_enrollment = ProgramEnrollmentFactory.create(
            user=self.user_2,
            program_uuid=self.program,
            external_user_key='0002',
        )
        self._assert_no_program_enrollment(self.user_1, self.program, refresh=False)
        self._assert_program_enrollment(self.user_2, self.program, '0002', refresh=False)

        with LogCapture() as logger:
            self.call_command(self.program, ('0001', self.user_1.username), ('0002', self.user_2.username))
            logger.check_present(
                (COMMAND_PATH, 'WARNING', get_existing_user_message(program_enrollment, self.user_2))
            )

        self._assert_program_enrollment(self.user_1, self.program, '0001')
        self._assert_program_enrollment(self.user_2, self.program, '0002')

    def test_enrollment_already_linked_to_different_user(self):
        self._create_waiting_enrollment(self.program, '0001')
        enrollment = ProgramEnrollmentFactory.create(
            program_uuid=self.program,
            external_user_key='0003',
        )
        user_3 = enrollment.user

        self._assert_no_program_enrollment(self.user_1, self.program, refresh=False)
        self._assert_no_program_enrollment(self.user_2, self.program, refresh=False)
        self._assert_program_enrollment(user_3, self.program, '0003', refresh=False)

        with LogCapture() as logger:
            self.call_command(self.program, ('0001', self.user_1.username), ('0003', self.user_2.username))
            logger.check_present(
                (COMMAND_PATH, 'WARNING', get_existing_user_message(enrollment, self.user_2))
            )

        self._assert_program_enrollment(self.user_1, self.program, '0001')
        self._assert_no_program_enrollment(self.user_2, self.program)
        self._assert_program_enrollment(user_3, self.program, '0003')

    def test_error_enrolling_in_course(self):
        nonexistant_course = CourseKey.from_string('course-v1:edX+Zilch+Bupkis')

        program_enrollment_1 = self._create_waiting_enrollment(self.program, '0001')
        self._create_waiting_course_enrollment(program_enrollment_1, nonexistant_course)
        self._create_waiting_course_enrollment(program_enrollment_1, self.animal_course)

        program_enrollment_2 = self._create_waiting_enrollment(self.program, '0002')
        self._create_waiting_course_enrollment(program_enrollment_2, nonexistant_course)
        self._create_waiting_course_enrollment(program_enrollment_2, self.animal_course)

        msg_1 = COURSE_ENROLLMENT_ERR_TPL.format(user=self.user_1.username, course=nonexistant_course)
        msg_2 = COURSE_ENROLLMENT_ERR_TPL.format(user=self.user_2.username, course=nonexistant_course)
        with LogCapture() as logger:
            self.call_command(self.program, ('0001', self.user_1.username), ('0002', self.user_2.username))
            logger.check_present((COMMAND_PATH, 'WARNING', msg_1))
            logger.check_present((COMMAND_PATH, 'WARNING', msg_2))

        self._assert_user_enrolled_in_program_courses(self.user_1, self.program, self.animal_course)
        self._assert_user_enrolled_in_program_courses(self.user_2, self.program, self.animal_course)
