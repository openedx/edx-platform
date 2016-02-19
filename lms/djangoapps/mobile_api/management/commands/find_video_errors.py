"""
Command to find video pipeline/migration/etc errors.
"""
# pylint: disable=global-statement
from collections import defaultdict
import csv
import logging

from django.core.management.base import BaseCommand, CommandError
from edxval.api import get_videos_for_course
from lms.djangoapps.course_api.blocks.transformers.student_view import StudentViewTransformer
from lms.djangoapps.course_blocks.api import get_course_in_cache
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


log = logging.getLogger(__name__)


LOG_TOTAL_NUMBER_OF_VIDEOS = False
LOG_NUMBER_OF_VIDEOS_PER_COURSE = False
LOG_PER_COURSE_STATS = False

LOG_COURSES_WITH_VIDEOS_WITHOUT_EDX_VIDEO_ID = False
LOG_COURSES_WITH_VIDEOS_WITHOUT_BOUND_COURSE = False

LOG_VIDEO_BLOCKS_WITHOUT_EDX_VIDEO_ID = False
LOG_VIDEO_BLOCKS_WITHOUT_BOUND_COURSE = False


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms find_video_errors --all --settings=devstack
        $ ./manage.py lms find_video_errors 'edX/DemoX/Demo_Course' --settings=devstack
    """
    args = '<course_id course_id ...>'
    help = 'Find and reports video-related errors in one or more courses.'

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        parser.add_argument(
            '--all',
            help='Find video-related stats for all courses.',
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
            default=-0,
            type=int,
        )
        parser.add_argument(
            '--end',
            help='Ending index of course.',
            default=0,
            type=int,
        )
        parser.add_argument(
            '--total_num_videos',
            help='Count total number of videos.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--num_videos_per_course',
            help='Count number of videos in each course.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--log_per_course_stats',
            help='Log video statistics for each course. Not needed if CSV output.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--log_videos_without_id',
            help='Log block keys of videos without edx video ids.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--log_videos_without_course',
            help='Log block keys of videos that are not bound to a course.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--log_courses_with_videos_without_id',
            help='Log course keys of courses with videos without edx video ids. Not needed if CSV output.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--log_courses_with_videos_without_course',
            help='Log course keys of courses with videos that are not bound to a course. Not needed if CSV output.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--mobile_only',
            help='Filter for courses that are designated as mobile available.',
            action='store_true',
            default=False,
        )
        parser.add_argument(
            '--csv',
            help='Output Course Video Stats to given CSV file.'
        )

    def handle(self, *args, **options):

        try:
            self._handle_logging_options(options)

            if options.get('all'):
                filter_ = None
                if options.get('mobile_only'):
                    filter_ = {'mobile_available': True}
                course_keys = [course.id for course in CourseOverview.get_all_courses(filter_=filter_)]
                end = options.get('end') or len(course_keys)
                course_keys = course_keys[options['start']:end]
            else:
                if len(args) < 1:
                    raise CommandError('At least one course or --all must be specified.')
                try:
                    course_keys = [CourseKey.from_string(arg) for arg in args]
                except InvalidKeyError:
                    raise CommandError('Invalid key specified.')

            log.critical('Reporting on video errors for %d courses.', len(course_keys))

            video_stats = _CourseVideoStats()
            for course_key in course_keys:
                try:
                    self._report_video_stats_in_course(course_key, video_stats)

                except Exception as ex:  # pylint: disable=broad-except
                    log.exception(
                        'An error occurred while reporting video-related errors in course %s: %s',
                        unicode(course_key),
                        ex.message,
                    )

            log.critical('Finished reporting on video errors.')

            if options.get('csv'):
                try:
                    video_stats.serialize_to_csv(options['csv'])
                except Exception as ex:  # pylint: disable=broad-except
                    log.exception('An error occurred while outputing CSV: %s', ex.message)

            log.critical('Video Error data: %s', unicode(video_stats))

        except Exception as error:
            raise CommandError(error.message)

    def _handle_logging_options(self, options):
        """
        Update settings for all options related to logging.
        """
        if options.get('verbose'):
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.CRITICAL)

        global LOG_TOTAL_NUMBER_OF_VIDEOS, LOG_NUMBER_OF_VIDEOS_PER_COURSE, LOG_PER_COURSE_STATS
        if options.get('total_num_videos'):
            LOG_TOTAL_NUMBER_OF_VIDEOS = True

        if options.get('num_videos_per_course'):
            LOG_NUMBER_OF_VIDEOS_PER_COURSE = True

        if options.get('log_per_course_stats'):
            LOG_PER_COURSE_STATS = True

        global LOG_VIDEO_BLOCKS_WITHOUT_EDX_VIDEO_ID, LOG_VIDEO_BLOCKS_WITHOUT_BOUND_COURSE
        if options.get('log_videos_without_id'):
            LOG_VIDEO_BLOCKS_WITHOUT_EDX_VIDEO_ID = True

        if options.get('log_videos_without_course'):
            LOG_VIDEO_BLOCKS_WITHOUT_BOUND_COURSE = True

        global LOG_COURSES_WITH_VIDEOS_WITHOUT_EDX_VIDEO_ID, LOG_COURSES_WITH_VIDEOS_WITHOUT_BOUND_COURSE
        if options.get('log_courses_with_videos_without_id'):
            LOG_COURSES_WITH_VIDEOS_WITHOUT_EDX_VIDEO_ID = True

        if options.get('log_courses_with_videos_without_course'):
            LOG_COURSES_WITH_VIDEOS_WITHOUT_BOUND_COURSE = True

    def _report_video_stats_in_course(self, course_key, video_stats):
        """
        Reports on video errors in the given course.
        """
        log.info('Video error check starting for course %s.', unicode(course_key))

        block_structure = get_course_in_cache(course_key)
        edx_video_ids_in_val = self._get_edx_video_ids_bound_to_course(course_key)

        for block_key in block_structure.get_block_keys():
            if block_key.category != 'video':
                continue
            video_stats.on_video_found(course_key)
            edx_video_id = self._get_edx_video_id(block_structure, block_key)
            if not edx_video_id:
                video_stats.on_no_edx_video_id(course_key, block_key)
            if edx_video_id not in edx_video_ids_in_val:
                video_stats.on_course_not_bound_to_video(course_key, block_key)

        log.info('Video error check complete for course %s.', unicode(course_key))

    def _get_edx_video_id(self, block_structure, block_key):
        """
        Returns the edx_video_id for the given block.
        """
        return block_structure.get_transformer_block_field(
            block_key,
            StudentViewTransformer,
            StudentViewTransformer.STUDENT_VIEW_DATA,
        )['edx_video_id']

    def _get_edx_video_ids_bound_to_course(self, course_key):
        """
        Returns the list of edx_video_ids bound to the given course in VAL.
        """
        return [video['edx_video_id'] for video in get_videos_for_course(course_key)]


class PrettyDefaultDict(defaultdict):
    """
    Wraps defaultdict to provide a better string representation.
    """
    __repr__ = dict.__repr__


class _CourseStats(object):
    """
    Class for aggregated DAG data for a specific course run.
    """
    def __init__(self):
        self.num_of_total_videos = 0
        self.num_of_videos_without_edx_video_id = 0
        self.num_of_videos_without_bound_course = 0

        if LOG_VIDEO_BLOCKS_WITHOUT_EDX_VIDEO_ID:
            self.videos_without_edx_video_id = []

        if LOG_VIDEO_BLOCKS_WITHOUT_BOUND_COURSE:
            self.videos_without_bound_course = []

    def __repr__(self):
        return repr(vars(self))
        # return json.dumps(self.__dict__, sort_keys=True, indent=4)

    def on_video_found(self):
        """
        Updates data for when a video block is found.
        """
        self.num_of_total_videos += 1

    def on_no_edx_video_id(self, block_key):
        """
        Updates error data for the given block.
        """
        self.num_of_videos_without_edx_video_id += 1
        if LOG_VIDEO_BLOCKS_WITHOUT_EDX_VIDEO_ID:
            self.videos_without_edx_video_id.append(unicode(block_key))

    def on_course_not_bound_to_video(self, block_key):
        """
        Updates error data for the given block.
        """
        self.num_of_videos_without_bound_course += 1
        if LOG_VIDEO_BLOCKS_WITHOUT_BOUND_COURSE:
            self.videos_without_bound_course.append(unicode(block_key))


class _CourseVideoStats(object):
    """
    Class for aggregated Video Error data.
    """
    def __init__(self):
        self.total_num_of_courses_with_errors = 0
        self.total_num_of_courses_without_edx_video_id = 0
        self.total_num_of_courses_without_bound_course = 0

        self.courses_without_edx_video_id = set()
        self.courses_without_bound_course = set()

        if LOG_TOTAL_NUMBER_OF_VIDEOS:
            self.total_num_of_videos = 0
        self.total_num_of_videos_without_edx_video_id = 0
        self.total_num_of_videos_without_bound_course = 0

        self.stats_by_course = PrettyDefaultDict(_CourseStats)

    def __repr__(self):
        self_vars = vars(self).copy()

        if not LOG_COURSES_WITH_VIDEOS_WITHOUT_EDX_VIDEO_ID:
            self_vars.pop('courses_without_edx_video_id', None)

        if not LOG_COURSES_WITH_VIDEOS_WITHOUT_BOUND_COURSE:
            self_vars.pop('courses_without_bound_course', None)

        if not LOG_PER_COURSE_STATS:
            self_vars.pop('stats_by_course', None)

        return repr(self_vars)
        # return json.dumps(self_vars, sort_keys=True, indent=4)

    def on_video_found(self, course_key):
        """
        Updates data for when a video block is found.
        """
        if LOG_TOTAL_NUMBER_OF_VIDEOS:
            self.total_num_of_videos += 1

        if LOG_NUMBER_OF_VIDEOS_PER_COURSE:
            self.stats_by_course[unicode(course_key)].on_video_found()

    def on_no_edx_video_id(self, course_key, block_key):
        """
        Updates error data for the given block.
        """
        self.total_num_of_videos_without_edx_video_id += 1

        self._update_total_num_courses_with_errors(course_key)

        if unicode(course_key) not in self.courses_without_edx_video_id:
            self.courses_without_edx_video_id.add(unicode(course_key))
            self.total_num_of_courses_without_edx_video_id += 1

        self.stats_by_course[unicode(course_key)].on_no_edx_video_id(block_key)

    def on_course_not_bound_to_video(self, course_key, block_key):
        """
        Updates error data for the given block.
        """
        self.total_num_of_videos_without_bound_course += 1

        self._update_total_num_courses_with_errors(course_key)

        if unicode(course_key) not in self.courses_without_bound_course:
            self.courses_without_bound_course.add(unicode(course_key))
            self.total_num_of_courses_without_bound_course += 1

        self.stats_by_course[unicode(course_key)].on_course_not_bound_to_video(block_key)

    def _update_total_num_courses_with_errors(self, course_key):
        """
        Updates count of courses with errors.
        """
        course_key_string = unicode(course_key)
        if (
                course_key_string not in self.courses_without_edx_video_id and
                course_key_string not in self.courses_without_bound_course
        ):
            self.total_num_of_courses_with_errors += 1

    def serialize_to_csv(self, csv_file_name):
        """
        Serializes the video stats to a new csv file with the provided name,
        overriding any existing file.
        """
        with open(csv_file_name, 'w') as csv_file:
            first_course_stat = next(iter(self.stats_by_course.values()))
            fieldnames = ['course_id'] + first_course_stat.__dict__.keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for course_id, course_stat in self.stats_by_course.iteritems():
                writer.writerow(
                    dict([('course_id', course_id)] + course_stat.__dict__.items())
                )
