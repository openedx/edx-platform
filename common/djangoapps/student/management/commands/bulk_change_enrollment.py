"""Management command to change many user enrollments at once."""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from optparse import make_option

from course_modes.models import CourseMode
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Command(BaseCommand):
    """Management command to change many user enrollments at once."""

    help = """
    Change the enrollment status for all users enrolled in a
    particular mode for a course. Similar to the change_enrollment
    script, but more useful for bulk moves.

    Example:

    Change enrollment for all audit users to honor in the given course.
        $ ... bulk_change_enrollment -c course-v1:SomeCourse+SomethingX+2016 --from_mode audit --to_mode honor --commit

    Without the --commit option, the command will have no effect.
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '-f', '--from_mode',
            dest='from_mode',
            default=None,
            help='move from this enrollment mode'
        ),
        make_option(
            '-t', '--to_mode',
            dest='to_mode',
            default=None,
            help='move to this enrollment mode'
        ),
        make_option(
            '-c', '--course',
            dest='course',
            default=None,
            help='the course to change enrollments in'
        ),
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='display what will be done without any effect'
        )
    )

    def handle(self, *args, **options):
        course_id = options.get('course')
        from_mode = options.get('from_mode')
        to_mode = options.get('to_mode')
        commit = options.get('commit')

        if course_id is None:
            raise CommandError('No course ID given.')
        if from_mode is None or to_mode is None:
            raise CommandError('Both `from` and `to` course modes must be given.')

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise CommandError('Course ID {} is invalid.'.format(course_id))

        if modulestore().get_course(course_key) is None:
            raise CommandError('The given course {} does not exist.'.format(course_id))

        if CourseMode.mode_for_course(course_key, to_mode) is None:
            raise CommandError('The given mode to move users into ({}) does not exist.'.format(to_mode))

        course_key_str = unicode(course_key)

        try:
            course_enrollments = CourseEnrollment.objects.filter(course_id=course_key, mode=from_mode)
            logger.info(
                'Moving %d users from %s to %s in course %s.',
                course_enrollments.count(), from_mode, to_mode, course_key_str
            )
            if not commit:
                logger.info('Dry run, changes have not been saved. Run again with "commit" argument to save changes')
                raise Exception('The --commit flag was not given; forcing rollback.')
            with transaction.atomic():
                # call `change_mode` which will change the mode and also emit tracking event
                for enrollment in course_enrollments:
                    enrollment.change_mode(mode=to_mode)

            logger.info('Finished moving users from %s to %s in course %s.', from_mode, to_mode, course_key_str)
        except Exception:  # pylint: disable=broad-except
            logger.info('No users moved.')
