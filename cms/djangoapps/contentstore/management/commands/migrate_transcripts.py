"""
Command to migrate transcripts to django storage.
"""

import logging
from django.core.management import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from cms.djangoapps.contentstore.tasks import (
    DEFAULT_ALL_COURSES,
    DEFAULT_FORCE_UPDATE,
    DEFAULT_COMMIT,
    enqueue_async_migrate_transcripts_tasks
)
from openedx.core.lib.command_utils import get_mutually_exclusive_required_option, parse_course_keys
from openedx.core.djangoapps.video_config.models import TranscriptMigrationSetting
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py cms migrate_transcripts --all-courses --force-update --commit
        $ ./manage.py cms migrate_transcripts --course-id 'Course1' --course-id 'Course2' --commit
        $ ./manage.py cms migrate_transcripts --from-settings
    """
    help = 'Migrates transcripts to S3 for one or more courses.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--course-id', '--course_id',
            dest='course_ids',
            action='append',
            help=u'Migrates transcripts for the list of courses.'
        )
        parser.add_argument(
            '--all-courses', '--all', '--all_courses',
            dest='all_courses',
            action='store_true',
            default=DEFAULT_ALL_COURSES,
            help=u'Migrates transcripts to the configured django storage for all courses.'
        )
        parser.add_argument(
            '--from-settings', '--from_settings',
            dest='from_settings',
            help='Migrate Transcripts with settings set via django admin',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--force-update', '--force_update',
            dest='force_update',
            action='store_true',
            default=DEFAULT_FORCE_UPDATE,
            help=u'Force migrate transcripts for the requested courses, overwrite if already present.'
        )
        parser.add_argument(
            '--commit',
            dest='commit',
            action='store_true',
            default=DEFAULT_COMMIT,
            help=u'Commits the discovered video transcripts to django storage. '
                 u'Without this flag, the command will return the transcripts discovered for migration.'
        )

    def _parse_course_key(self, raw_value):
        """ Parses course key from string """
        try:
            result = CourseKey.from_string(raw_value)
        except InvalidKeyError:
            raise CommandError("Invalid course_key: '%s'." % raw_value)

        if not isinstance(result, CourseLocator):
            raise CommandError(u"Argument {0} is not a course key".format(raw_value))

        return result

    def _get_migration_options(self, options):
        """
        Returns the command arguments configured via django admin.
        """
        force_update = options['force_update']
        commit = options['commit']
        courses_mode = get_mutually_exclusive_required_option(options, 'course_ids', 'all_courses', 'from_settings')
        if courses_mode == 'all_courses':
            course_keys = [course.id for course in modulestore().get_course_summaries()]
        elif courses_mode == 'course_ids':
            course_keys = map(self._parse_course_key, options['course_ids'])
        else:
            if self._latest_settings().all_courses:
                course_keys = [course.id for course in modulestore().get_course_summaries()]
            else:
                course_keys = parse_course_keys(self._latest_settings().course_ids.split())
            force_update = self._latest_settings().force_update
            commit = self._latest_settings().commit

        return course_keys, force_update, commit

    def _latest_settings(self):
        """
        Return the latest version of the TranscriptMigrationSetting
        """
        return TranscriptMigrationSetting.current()

    def handle(self, *args, **options):
        """
        Invokes the migrate transcripts enqueue function.
        """
        course_keys, force_update, commit = self._get_migration_options(options)
        command_run = self._latest_settings().increment_run() if commit else -1
        enqueue_async_migrate_transcripts_tasks(
            course_keys=course_keys, commit=commit, command_run=command_run, force_update=force_update
        )
