"""
Management command to migrate existing course discussion topics to new provider.
"""
import logging
from textwrap import dedent

from django.core.management import BaseCommand
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_apps.tasks import cache_all_course_apps_status, update_course_apps_status
from openedx.core.djangoapps.discussions.models import DiscussionTopicLink, Provider
from openedx.core.djangoapps.discussions.utils import get_accessible_discussion_xblocks_by_course_id

log = logging.getLogger("migrate_discussion_topics")

class Command(BaseCommand):
    """
    Command to migrate existing course discussion topics to new provider.

    This command is currently designed for testing only.


    Examples:

        ./manage.py lms migrate_discussion_topics course-v1:edX+DemoX+Demo_Course
    """
    help = dedent(__doc__)

    def add_arguments(self, parser):
        """ Add argument to the command parser. """
        parser.add_argument('course_key', type=CourseKey.from_string)

    def handle(self, *args, **options):
        """
        Handle the cache course app status command.
        """
        course_key = options['course_key']
        blocks = get_accessible_discussion_xblocks_by_course_id(course_key, include_all=True)
        for block in blocks:
            if block.parent.category == 'vertical':
                obj, created = DiscussionTopicLink.objects.update_or_create(
                    context_key=course_key,
                    usage_key=block.parent,
                    provider_id=Provider.OPEN_EDX,
                    defaults=dict(
                        title=block.get_parent().display_name,
                        external_id=block.discussion_id,
                        enabled_in_context=True,
                    )
                )
                log.info(
                    '%s topic link with external id "%s" for unit "%s"',
                    "Creating" if created else "Updating",
                    block.discussion_id,
                    block.parent,
                )
