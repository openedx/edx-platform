""" Command line script to change user enrollments. """

import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from optparse import make_option

from student.models import CourseEnrollment, User

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class RollbackException(Exception):
    """
    Exception raised explicitly to cause a database transaction rollback.
    """
    pass


class Command(BaseCommand):

    help = """
    Changes the enrollment status for students that meet
    the criteria specified by the parameters to this command.

    Example:

        Change enrollment for users joe, frank, and bill from audit to honor:

          $ ... change_enrollment -u joe,frank,bill -c some/course/id --from audit --to honor

        Or

          $ ... change_enrollment -e "joe@example.com,frank@example.com,bill@example.com" -c some/course/id --from audit --to honor

        See what would have been changed from audit to honor without making that change

          $ ... change_enrollment -u joe,frank,bill -c some/course/id --from audit --to honor -n

    """

    option_list = BaseCommand.option_list + (
        make_option('-f', '--from',
                    metavar='FROM_MODE',
                    dest='from_mode',
                    default=False,
                    help='move from this enrollment mode'),
        make_option('-t', '--to',
                    metavar='TO_MODE',
                    dest='to_mode',
                    default=False,
                    help='move to this enrollment mode'),
        make_option('-u', '--usernames',
                    metavar='USERNAME',
                    dest='username',
                    default=False,
                    help="Comma-separated list of usernames to move in the course"),
        make_option('-e', '--emails',
                    metavar='EMAIL',
                    dest='email',
                    default=False,
                    help="Comma-separated list of email addresses to move in the course"),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course_id',
                    default=False,
                    help="course id to use for transfer"),
        make_option('-n', '--noop',
                    action='store_true',
                    dest='noop',
                    default=False,
                    help="display what will be done but don't actually do anything")

    )

    def handle(self, *args, **options):
        error_users = []
        success_users = []

        if not options['course_id']:
            raise CommandError('You must specify a course id for this command')
        if not options['from_mode'] or not options['to_mode']:
            raise CommandError('You must specify a "to" and "from" mode as parameters')

        try:
            course_key = CourseKey.from_string(options['course_id'])
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(options['course_id'])

        enrollment_args = dict(
            course_id=course_key,
            mode=options['from_mode']
        )

        if options['username']:
            self.update_enrollments('username', enrollment_args, options, error_users, success_users)

        if options['email']:
            self.update_enrollments('email', enrollment_args, options, error_users, success_users)

        self.report(error_users, success_users)

    def update_enrollments(self, identifier, enrollment_args, options, error_users, success_users):
        """ Update enrollments for a specific user identifier (email or username). """
        users = options[identifier].split(",")
        for identified_user in users:
            logger.info(identified_user)
            try:
                user_args = {
                    identifier: identified_user
                }

                enrollment_args['user'] = User.objects.get(**user_args)
                enrollments = CourseEnrollment.objects.filter(**enrollment_args)

                with transaction.atomic():
                    for enrollment in enrollments:
                        enrollment.update_enrollment(mode=options['to_mode'])
                        enrollment.save()

                    if options['noop']:
                        raise RollbackException('Forced rollback.')

            except RollbackException:
                success_users.append(identified_user)
                continue
            except Exception as exception:  # pylint: disable=broad-except
                error_users.append((identified_user, exception))
                continue

            success_users.append(identified_user)
            logger.info('Updated user [%s] to mode [%s]', identified_user, options['to_mode'])

    def report(self, error_users, success_users):
        """ Log and overview of the results of the command. """
        total_users = len(success_users) + len(error_users)
        logger.info('Successfully updated %i out of %i users', len(success_users), total_users)
        if len(error_users) > 0:
            logger.info('The following %i user(s) not saved:', len(error_users))
            for user, error in error_users:
                logger.info('user: [%s] reason: [%s] %s', user, type(error).__name__, error.message)
