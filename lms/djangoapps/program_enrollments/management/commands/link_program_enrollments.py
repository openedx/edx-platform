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
NO_PROGRAM_ENROLLMENT_TPL = (u'No program enrollment found for program uuid={program_uuid} and external student '
                             'key={external_student_key}')
NO_LMS_USER_TPL = u'No user found with username {}'
COURSE_ENROLLMENT_ERR_TPL = u'Failed to enroll user {user} with waiting program course enrollment for course {course}'
EXISTING_USER_TPL = (u'Program enrollment with external_student_key={external_student_key} is already linked to '
                     u'{account_relation} account username={username}')


class Command(BaseCommand):
    """
    Management command to manually link ProgramEnrollments without an LMS user to an LMS user by username

    Usage:
        ./manage.py lms link_program_enrollments <program_uuid> <user_item>*
        where a <user_item> is a string formatted as <external_user_key>:<lms_username>

    Normally, program enrollments should be linked by the Django Social Auth post_save signal handler
    `lms.djangoapps.program_enrollments.signals.matriculate_learner`, but in the case that a partner does not
    have an IDP set up for learners to log in through, we need a way to link enrollments

    Provided a program uuid and a list of external_user_key:lms_username, this command will look up the matching
    program enrollments and users, and update the program enrollments with the matching user. If the program
    enrollment has course enrollments, we will enroll the user into their waiting program courses.

    If an external user key is specified twice, an exception will be raised and no enrollments will be modified.

    For each external_user_key:lms_username, if:
        - The user is not found
        - No enrollment is found for the given program and external_user_key
        - The enrollment already has a user
    An error message will be logged and the input will be skipped. All other inputs will be processed and
    enrollments updated.

    If there is an error while enrolling a user in a waiting program course enrollment, the error will be
    logged, but we will continue attempting to enroll the user in courses, and we will process all other
    input users
    """

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
                logger.warning(NO_PROGRAM_ENROLLMENT_TPL.format(
                    program_uuid=program_uuid,
                    external_student_key=external_student_key
                ))
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
        program_enrollments = ProgramEnrollment.bulk_read_by_student_key(
            program_uuid,
            external_student_keys
        ).prefetch_related(
            'program_course_enrollments'
        ).select_related('user')
        return {
            program_enrollment.external_user_key: program_enrollment
            for program_enrollment in program_enrollments
        }

    def get_lms_users(self, lms_usernames):
        """
        Does a bulk read of Users by username and returns a dict keyed by username
        """
        return {
            user.username: user
            for user in User.objects.filter(username__in=lms_usernames)
        }

    def link_program_enrollment(self, program_enrollment, user):
        """
        Attempts to link the given program enrollment to the given user
        If the enrollment has any program course enrollments, enroll the user in those courses as well
        """
        if program_enrollment.user:
            logger.warning(get_existing_user_message(program_enrollment, user))
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
                logger.warning(COURSE_ENROLLMENT_ERR_TPL.format(
                    user=user.username,
                    course=program_course_enrollment.course_key
                ))


def get_existing_user_message(program_enrollment, user):
    """
    Creates an error message that the specified program enrollment is already linked to an lms user
    """
    existing_username = program_enrollment.user.username
    external_student_key = program_enrollment.external_user_key
    return EXISTING_USER_TPL.format(
        external_student_key=external_student_key,
        account_relation='target' if program_enrollment.user.id == user.id else 'a different',
        username=existing_username,
    )
