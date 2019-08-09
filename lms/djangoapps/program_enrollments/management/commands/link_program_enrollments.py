""" Management command to link program enrollments and external student_keys to an LMS user """
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from lms.djangoapps.program_enrollments.models import ProgramEnrollment
from student.models import CourseEnrollmentException

logger = logging.getLogger(__name__)
User = get_user_model()

INCORRECT_PARAMETER_TPL = u'incorrectly formatted argument {}, must be in form <external user key>:<lms username>'
DUPLICATE_KEY_TPL = u'external user key {} provided multiple times'
NO_PROGRAM_ENROLLMENT_TPL = u'No program enrollment found for program uuid={} and external student key={}'
NO_LMS_USER_TPL = u'No user found with username {}'
COURSE_ENROLLMENT_FAILURE_TPL = u'Failed to enroll user {} with waiting program course enrollment for course {}'
EXISTING_USER_TPL = u'Program enrollment with external_student_key={} is already linked to {} account username={}'


class Command(BaseCommand):
    # pylint: disable=missing-docstring

    help = u'Manually links ProgramEnrollment records to LMS users'

    def add_arguments(self, parser):
        parser.add_argument(
            'program_uuid',
            help='the program in which we are linking enrollments to users',
        )
        parser.add_argument(
            'user_items',
            nargs='*',
            help='specify the users to link, in the format <external_student_key>:<lms_username>*',
        )

    # pylint: disable=arguments-differ
    @transaction.atomic
    def handle(self, program_uuid, user_items, *args, **options):
        ext_keys_to_usernames = self.parse_user_items(user_items)
        program_enrollments = self.get_program_enrollments(program_uuid, ext_keys_to_usernames.keys())
        users = self.get_lms_users(ext_keys_to_usernames.values())
        for external_student_key, username in ext_keys_to_usernames.items():
            program_enrollment = program_enrollments.get(external_student_key)
            if not program_enrollment:
                logger.warning(NO_PROGRAM_ENROLLMENT_TPL.format(program_uuid, external_student_key))
                continue

            user = users.get(username)
            if not user:
                logger.warning(NO_LMS_USER_TPL.format(username))
                continue

            self.link_program_enrollment(program_enrollment, user)

    def parse_user_items(self, user_items):
        """
        Params:
            list of strings in the format 'external_user_key:lms_username'
        Returns:
            dict mapping external user keys to lms usernames
        """
        result = {}
        for user_item in user_items:
            split_args = user_item.split(':')
            if len(split_args) != 2:
                message = (INCORRECT_PARAMETER_TPL).format(user_item)
                raise CommandError(message)

            external_user_key = split_args[0]
            lms_username = split_args[1]
            if external_user_key in result:
                raise CommandError(DUPLICATE_KEY_TPL.format(external_user_key))

            result[external_user_key] = lms_username
        return result

    def get_program_enrollments(self, program_uuid, external_student_keys):
        """
        Does a bulk read of ProgramEnrollments for a given program and list of external student keys
        and returns a dict keyed by external student key
        """
        qs = ProgramEnrollment.bulk_read_by_student_key(program_uuid, external_student_keys)
        qs = qs.prefetch_related('program_course_enrollments')
        qs = qs.select_related('user')
        return {
            program_enrollment.external_user_key: program_enrollment
            for program_enrollment in qs.iterator()
        }

    def get_lms_users(self, lms_usernames):
        """
        Does a bulk read of Users by username and returns a dict keyed by username
        """
        return {
            user.username: user
            for user in User.objects.filter(username__in=lms_usernames).iterator()
        }

    def link_program_enrollment(self, program_enrollment, user):
        """
        Attempts to link the given program enrollment to the given user
        If the enrollment has any program course enrollments, enroll the user in those courses as well
        """
        if program_enrollment.user:
            self.log_existing_user_message(program_enrollment, user)
            return
        logger.info(u'Linking external student key {} and user {}'.format(
            program_enrollment.external_user_key,
            user.username
        ))
        program_enrollment.user = user
        program_enrollment.save()

        for program_course_enrollment in program_enrollment.program_course_enrollments.all():
            try:
                program_course_enrollment.enroll(user)
            except CourseEnrollmentException:
                logger.warning(COURSE_ENROLLMENT_FAILURE_TPL.format(
                    user.username,
                    program_course_enrollment.course_key
                ))

    def log_existing_user_message(self, program_enrollment, user):
        """
        Logs an error message that the specified program enrollment is already linked to an lms user
        """
        existing_username = program_enrollment.user.username
        external_student_key = program_enrollment.external_user_key
        logger.warning(EXISTING_USER_TPL.format(
            external_student_key,
            'target' if program_enrollment.user.id == user.id else 'a different',
            existing_username,
        ))
