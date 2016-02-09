"""
Command to load course blocks.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from ...api import get_course_in_cache


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms generate_course_blocks --all --settings=devstack
        $ ./manage.py lms generate_course_blocks 'edX/DemoX/Demo_Course' --settings=devstack
    """
    args = '<course_id course_id ...>'
    help = 'Generates and stores course blocks for one or more courses.'

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            '--all',
            help='Generate course blocks for all or specified courses.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--dags',
            help='Find and log DAGs for all or specified courses.',
            action='store_true',
            default=False,
        )

    def handle(self, *args, **options):

        if options.get('all'):
            course_keys = [course.id for course in modulestore().get_course_summaries()]
        else:
            if len(args) < 1:
                raise CommandError('At least one course or --all must be specified.')
            try:
                course_keys = [CourseKey.from_string(arg) for arg in args]
            except InvalidKeyError:
                raise CommandError('Invalid key specified.')

        log.info('Generating course blocks for %d courses.', len(course_keys))
        log.debug('Generating course blocks for the following courses: %s', course_keys)

        for course_key in course_keys:
            try:
                block_structure = get_course_in_cache(course_key)
                if options.get('dags'):
                    self._find_and_log_dags(block_structure, course_key)
            except Exception as ex:  # pylint: disable=broad-except
                log.exception(
                    'An error occurred while generating course blocks for %s: %s',
                    unicode(course_key),
                    ex.message,
                )

        log.info('Finished generating course blocks.')

    def _find_and_log_dags(self, block_structure, course_key):
        """
        Finds all DAGs within the given block structure.

        Arguments:
            BlockStructureBlockData - The block structure in which to find DAGs.
        """
        log.info('DAG check starting for course %s.', unicode(course_key))
        for block_key in block_structure.get_block_keys():
            parents = block_structure.get_parents(block_key)
            if len(parents) > 1:
                log.warning(
                    'DAG alert - %s has multiple parents: %s.',
                    unicode(block_key),
                    [unicode(parent) for parent in parents],
                )
        log.info('DAG check complete for course %s.', unicode(course_key))
