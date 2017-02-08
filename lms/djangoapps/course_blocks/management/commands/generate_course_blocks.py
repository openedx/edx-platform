"""
Command to load course blocks.
"""
import logging

from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore

import openedx.core.djangoapps.content.block_structure.api as api
import openedx.core.djangoapps.content.block_structure.tasks as tasks
import openedx.core.lib.block_structure.cache as cache
from openedx.core.lib.command_utils import (
    get_mutually_exclusive_required_option,
    validate_dependent_option,
    parse_course_keys,
)


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
            '--courses',
            dest='courses',
            nargs='+',
            help='Generate course blocks for the list of courses provided.',
        )
        parser.add_argument(
            '--all_courses',
            help='Generate course blocks for all courses, given the requested start and end indices.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--enqueue_task',
            help='Enqueue the tasks for asynchronous computation.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--routing_key',
            dest='routing_key',
            help='Routing key to use for asynchronous computation.',
        )
        parser.add_argument(
            '--force_update',
            help='Force update of the course blocks for the requested courses.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--start_index',
            help='Starting index of course list.',
            default=0,
            type=int,
        )
        parser.add_argument(
            '--end_index',
            help='Ending index of course list.',
            default=0,
            type=int,
        )

    def handle(self, *args, **options):

        courses_mode = get_mutually_exclusive_required_option(options, 'courses', 'all_courses')
        validate_dependent_option(options, 'routing_key', 'enqueue_task')
        validate_dependent_option(options, 'start_index', 'all_courses')
        validate_dependent_option(options, 'end_index', 'all_courses')

        if courses_mode == 'all_courses':
            course_keys = [course.id for course in modulestore().get_course_summaries()]
            if options.get('start_index'):
                end = options.get('end_index') or len(course_keys)
                course_keys = course_keys[options['start_index']:end]
        else:
            course_keys = parse_course_keys(options['courses'])

        self._set_log_levels(options)

        log.warning('STARTED generating Course Blocks for %d courses.', len(course_keys))
        self._generate_course_blocks(options, course_keys)
        log.warning('FINISHED generating Course Blocks for %d courses.', len(course_keys))

    def _set_log_levels(self, options):
        """
        Sets logging levels for this module and the block structure
        cache module, based on the given the options.
        """
        if options.get('verbosity') == 0:
            log_level = logging.CRITICAL
        elif options.get('verbosity') == 1:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        if options.get('verbosity') < 3:
            cache_log_level = logging.CRITICAL
        else:
            cache_log_level = logging.INFO

        log.setLevel(log_level)
        cache.logger.setLevel(cache_log_level)

    def _generate_course_blocks(self, options, course_keys):
        """
        Generates course blocks for the given course_keys per the given options.
        """

        for course_key in course_keys:
            try:
                log.info('STARTED generating Course Blocks for course: %s.', course_key)

                if options.get('enqueue_task'):
                    action = tasks.update_course_in_cache if options.get('force_update') else tasks.get_course_in_cache
                    task_options = {'routing_key': options['routing_key']} if options.get('routing_key') else {}
                    action.apply_async([unicode(course_key)], **task_options)
                else:
                    action = api.update_course_in_cache if options.get('force_update') else api.get_course_in_cache
                    action(course_key)

                log.info('FINISHED generating Course Blocks for course: %s.', course_key)
            except Exception as ex:  # pylint: disable=broad-except
                log.exception(
                    'An error occurred while generating course blocks for %s: %s',
                    unicode(course_key),
                    ex.message,
                )
