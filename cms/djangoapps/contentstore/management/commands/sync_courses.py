"""
Sync courses from catalog service.  This is used to setup a master's
integration environment.
"""
import logging
from textwrap import dedent

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys.edx.keys import CourseKey
from six import text_type

from cms.djangoapps.contentstore.management.commands.utils import user_from_str
from cms.djangoapps.contentstore.views.course import create_new_course_in_store
from openedx.core.djangoapps.catalog.utils import get_course_runs
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import DuplicateCourseError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to populate modulestore with courses from the discovery service.

    Example: ./manage.py cms sync_courses staff@example.com
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument('instructor')

    def get_user(self, user):
        """
        Return a User object.
        """
        try:
            user_object = user_from_str(user)
        except User.DoesNotExist:
            raise CommandError(u"No user {user} found.".format(user=user))
        return user_object

    def handle(self, *args, **options):
        """Execute the command"""
        instructor = self.get_user(options['instructor'])

        course_runs = get_course_runs()
        for course_run in course_runs:
            course_key = CourseKey.from_string(course_run.get('key'))
            fields = {
                "display_name": course_run.get('title')
            }

            try:
                new_course = create_new_course_in_store(
                    ModuleStoreEnum.Type.split,
                    instructor,
                    course_key.org,
                    course_key.course,
                    course_key.run,
                    fields,
                )
                logger.info(u"Created {}".format(text_type(new_course.id)))
            except DuplicateCourseError:
                logger.warning(
                    u"Course already exists for %s, %s, %s. Skipping",
                    course_key.org,
                    course_key.course,
                    course_key.run,
                )
