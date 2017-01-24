"""
Command to load course blocks.
"""
from collections import defaultdict
import logging

from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache, update_course_in_cache


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
        parser.add_argument(
            '--force',
            help='Force update of the course blocks for the requested courses.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--verbose',
            help='Enable verbose logging.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--start',
            help='Starting index of course.',
            default=0,
            type=int,
        )
        parser.add_argument(
            '--end',
            help='Ending index of course.',
            default=0,
            type=int,
        )

    def handle(self, *args, **options):

        if options.get('all'):
            course_keys = [course.id for course in modulestore().get_course_summaries()]
            if options.get('start'):
                end = options.get('end') or len(course_keys)
                course_keys = course_keys[options['start']:end]
        else:
            if len(args) < 1:
                raise CommandError('At least one course or --all must be specified.')
            try:
                course_keys = [CourseKey.from_string(arg) for arg in args]
            except InvalidKeyError:
                raise CommandError('Invalid key specified.')

        log.info('Generating course blocks for %d courses.', len(course_keys))

        if options.get('verbose'):
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.CRITICAL)

        dag_info = _DAGInfo()
        for course_key in course_keys:
            try:
                if options.get('force'):
                    block_structure = update_course_in_cache(course_key)
                else:
                    block_structure = get_course_in_cache(course_key)
                if options.get('dags'):
                    self._find_and_log_dags(block_structure, course_key, dag_info)
            except Exception as ex:  # pylint: disable=broad-except
                log.exception(
                    'An error occurred while generating course blocks for %s: %s',
                    unicode(course_key),
                    ex.message,
                )

        log.info('Finished generating course blocks.')

        if options.get('dags'):
            log.critical('DAG data: %s', unicode(dag_info))

    def _find_and_log_dags(self, block_structure, course_key, dag_info):
        """
        Finds all DAGs within the given block structure.

        Arguments:
            BlockStructureBlockData - The block structure in which to find DAGs.
        """
        for block_key in block_structure.get_block_keys():
            parents = block_structure.get_parents(block_key)
            if len(parents) > 1:
                dag_info.on_dag_found(course_key, block_key)
                log.warning(
                    'DAG alert - %s has multiple parents: %s.',
                    unicode(block_key),
                    [unicode(parent) for parent in parents],
                )


class PrettyDefaultDict(defaultdict):
    """
    Wraps defaultdict to provide a better string representation.
    """
    __repr__ = dict.__repr__


class _DAGBlockTypeInfo(object):
    """
    Class for aggregated DAG data for a specific block type.
    """
    def __init__(self):
        self.num_of_dag_blocks = 0

    def __repr__(self):
        return repr(vars(self))


class _DAGCourseInfo(object):
    """
    Class for aggregated DAG data for a specific course run.
    """
    def __init__(self):
        self.num_of_dag_blocks = 0
        self.dag_data_by_block_type = PrettyDefaultDict(_DAGBlockTypeInfo)

    def __repr__(self):
        return repr(vars(self))

    def on_dag_found(self, block_key):
        """
        Updates DAG collected data for the given block.
        """
        self.num_of_dag_blocks += 1
        self.dag_data_by_block_type[block_key.category].num_of_dag_blocks += 1


class _DAGInfo(object):
    """
    Class for aggregated DAG data.
    """
    def __init__(self):
        self.total_num_of_dag_blocks = 0
        self.total_num_of_dag_courses = 0
        self.dag_data_by_course = PrettyDefaultDict(_DAGCourseInfo)
        self.dag_data_by_block_type = PrettyDefaultDict(_DAGBlockTypeInfo)

    def __repr__(self):
        return repr(vars(self))

    def on_dag_found(self, course_key, block_key):
        """
        Updates DAG collected data for the given block.
        """
        self.total_num_of_dag_blocks += 1
        if course_key not in self.dag_data_by_course:
            self.total_num_of_dag_courses += 1
        self.dag_data_by_course[unicode(course_key)].on_dag_found(block_key)
        self.dag_data_by_block_type[block_key.category].num_of_dag_blocks += 1
