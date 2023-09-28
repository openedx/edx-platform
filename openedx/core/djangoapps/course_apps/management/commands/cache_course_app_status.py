"""
Management command to cache course apps status in the databse.
"""

from textwrap import dedent

from django.core.management import BaseCommand
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_apps.tasks import cache_all_course_apps_status, update_course_apps_status


class Command(BaseCommand):
    """
    Command to cache status of course apps to the database to speed up queries.

    If no arguments are provided, update cache for all courses.
    This can be run as a one-off command. If new plugins are installed or existing plugins are uninstalled, the
    status of those will be cached on first access so re-running this isn't necessary.


    Examples:

        ./manage.py lms cache_course_app_status
        ./manage.py lms cache_course_app_status course-v1:edX+DemoX+Demo_Course course-v1:edX+CS101+T22021
    """
    help = dedent(__doc__)

    def add_arguments(self, parser):
        """ Add argument to the command parser. """
        parser.add_argument('course_keys', type=CourseKey.from_string, nargs='*')

    def handle(self, *args, **options):
        """
        Handle the cache course app status command.
        """
        course_keys = options['course_keys']
        if course_keys:
            for course_key in CourseOverview.objects.filter(id__in=course_keys).values_list('id', flat=True):
                update_course_apps_status.delay(str(course_key))
        else:
            cache_all_course_apps_status.delay()
