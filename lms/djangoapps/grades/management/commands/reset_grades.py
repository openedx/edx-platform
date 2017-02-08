"""
Reset persistent grades for learners.
"""
from datetime import datetime
import logging
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from openedx.core.lib.command_utils import get_mutually_exclusive_required_option, parse_course_keys
from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentCourseGrade


log = logging.getLogger(__name__)


DATE_FORMAT = "%Y-%m-%d %H:%M"


class Command(BaseCommand):
    """
    Reset persistent grades for learners.
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--dry_run',
            action='store_true',
            default=False,
            dest='dry_run',
            help="Output what we're going to do, but don't actually do it. To actually delete, use --delete instead."
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            default=False,
            dest='delete',
            help="Actually perform the deletions of the course. For a Dry Run, use --dry_run instead."
        )
        parser.add_argument(
            '--courses',
            dest='courses',
            nargs='+',
            help='Reset persistent grades for the list of courses provided.',
        )
        parser.add_argument(
            '--all_courses',
            action='store_true',
            dest='all_courses',
            default=False,
            help='Reset persistent grades for all courses.',
        )
        parser.add_argument(
            '--modified_start',
            dest='modified_start',
            help='Starting range for modified date (inclusive): e.g. "2016-08-23 16:43"',
        )
        parser.add_argument(
            '--modified_end',
            dest='modified_end',
            help='Ending range for modified date (inclusive): e.g. "2016-12-23 16:43"',
        )

    def handle(self, *args, **options):
        course_keys = None
        modified_start = None
        modified_end = None

        run_mode = get_mutually_exclusive_required_option(options, 'delete', 'dry_run')
        courses_mode = get_mutually_exclusive_required_option(options, 'courses', 'all_courses')

        if options.get('modified_start'):
            modified_start = datetime.strptime(options['modified_start'], DATE_FORMAT)

        if options.get('modified_end'):
            if not modified_start:
                raise CommandError('Optional value for modified_end provided without a value for modified_start.')
            modified_end = datetime.strptime(options['modified_end'], DATE_FORMAT)

        if courses_mode == 'courses':
            course_keys = parse_course_keys(options['courses'])

        log.info("reset_grade: Started in %s mode!", run_mode)

        operation = self._query_grades if run_mode == 'dry_run' else self._delete_grades

        operation(PersistentSubsectionGrade, course_keys, modified_start, modified_end)
        operation(PersistentCourseGrade, course_keys, modified_start, modified_end)

        log.info("reset_grade: Finished in %s mode!", run_mode)

    def _delete_grades(self, grade_model_class, *args, **kwargs):
        """
        Deletes the requested grades in the given model, filtered by the provided args and kwargs.
        """
        grades_query_set = grade_model_class.query_grades(*args, **kwargs)
        num_rows_to_delete = grades_query_set.count()

        log.info("reset_grade: Deleting %s: %d row(s).", grade_model_class.__name__, num_rows_to_delete)

        grade_model_class.delete_grades(*args, **kwargs)

        log.info("reset_grade: Deleted %s: %d row(s).", grade_model_class.__name__, num_rows_to_delete)

    def _query_grades(self, grade_model_class, *args, **kwargs):
        """
        Queries the requested grades in the given model, filtered by the provided args and kwargs.
        """
        total_for_all_courses = 0

        grades_query_set = grade_model_class.query_grades(*args, **kwargs)
        grades_stats = grades_query_set.values('course_id').order_by().annotate(total=Count('course_id'))

        for stat in grades_stats:
            total_for_all_courses += stat['total']
            log.info(
                "reset_grade: Would delete %s for COURSE %s: %d row(s).",
                grade_model_class.__name__,
                stat['course_id'],
                stat['total'],
            )

        log.info(
            "reset_grade: Would delete %s in TOTAL: %d row(s).",
            grade_model_class.__name__,
            total_for_all_courses,
        )
