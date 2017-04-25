"""Management command to change many user enrollments at once."""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from optparse import make_option
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

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
            '-o', '--org',
            dest='org',
            default=None,
            help='all courses belonging to this org will be selected for changing the enrollments'
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
        org = options.get('org')
        from_mode = options.get('from_mode')
        to_mode = options.get('to_mode')
        commit = options.get('commit')

        if (not course_id and not org) or (course_id and org):
            raise CommandError('You must provide either a course ID or an org, but not both.')

        if from_mode is None or to_mode is None:
            raise CommandError('Both `from` and `to` course modes must be given.')

        course_keys = []
        if course_id:
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                raise CommandError('Course ID {} is invalid.'.format(course_id))

            if modulestore().get_course(course_key) is None:
                raise CommandError('The given course {} does not exist.'.format(course_id))

            course_keys.append(course_key)
        else:
            course_keys = [course.id for course in CourseOverview.get_all_courses(orgs=[org])]
            if not course_keys:
                raise CommandError('No courses exist for the org "{}".'.format(org))

        for course_key in course_keys:
            self.move_users_for_course(course_key, from_mode, to_mode, commit)

        if not commit:
            logger.info('Dry run, changes have not been saved. Run again with "commit" argument to save changes')

    def move_users_for_course(self, course_key, from_mode, to_mode, commit):
        """
        Change the enrollment mode of users for a course.

        Arguments:
            course_key (CourseKey): to lookup the course.
            from_mode (str): the enrollment mode to change.
            to_mode (str): the enrollment mode to change to.
            commit (bool): required to make the change to the database. Otherwise
                                     just a count will be displayed.
        """
        unicode_course_key = unicode(course_key)
        if CourseMode.mode_for_course(course_key, to_mode) is None:
            logger.info('Mode ({}) does not exist for course ({}).'.format(to_mode, unicode_course_key))
            return

        course_enrollments = CourseEnrollment.objects.filter(course_id=course_key, mode=from_mode)
        logger.info(
            'Moving %d users from %s to %s in course %s.',
            course_enrollments.count(), from_mode, to_mode, unicode_course_key
        )
        if commit:
            # call `change_mode` which will change the mode and also emit tracking event
            for enrollment in course_enrollments:
                with transaction.atomic():
                    enrollment.change_mode(mode=to_mode)

            logger.info('Finished moving users from %s to %s in course %s.', from_mode, to_mode, unicode_course_key)
