"""
Management command to cache course apps status in the databse.
"""

from textwrap import dedent

from django.core.management import BaseCommand

from openedx.core.djangoapps.course_apps.tasks import cache_all_course_apps_status


class Command(BaseCommand):
    """
    Command to cache status of course apps to the database to speed up queries.

    This can be run as a one-off command. If new plugins are installed or existing plugins are uninstalled, the
    status of those will be cached on first access so re-running this isn't necessary.
    """
    help = dedent(__doc__)

    def handle(self, *args, **options):
        cache_all_course_apps_status.delay()
