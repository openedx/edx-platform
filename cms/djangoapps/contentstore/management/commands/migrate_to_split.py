"""
Django management command to migrate a course from the old Mongo modulestore
to the new split-Mongo modulestore.
"""


from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from cms.djangoapps.contentstore.management.commands.utils import user_from_str
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.split_migrator import SplitMigrator


class Command(BaseCommand):
    """
    Migrate a course from old-Mongo to split-Mongo. It reuses the old course id except where overridden.
    """

    help = "Migrate a course from old-Mongo to split-Mongo. The new org, course, and run will " \
           "default to the old one unless overridden."

    def add_arguments(self, parser):
        parser.add_argument('course_key')
        parser.add_argument('email')
        parser.add_argument('--org', help='New org to migrate to.')
        parser.add_argument('--course', help='New course key to migrate to.')
        parser.add_argument('--run', help='New run to migrate to.')

    def parse_args(self, **options):
        """
        Return a 5-tuple of passed in values for (course_key, user, org, course, run).
        """
        try:
            course_key = CourseKey.from_string(options['course_key'])
        except InvalidKeyError:
            raise CommandError("Invalid location string")

        try:
            user = user_from_str(options['email'])
        except User.DoesNotExist:
            raise CommandError(u"No user found identified by {}".format(options['email']))

        return course_key, user.id, options['org'], options['course'], options['run']

    def handle(self, *args, **options):
        course_key, user, org, course, run = self.parse_args(**options)

        migrator = SplitMigrator(
            source_modulestore=modulestore(),
            split_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split),
        )

        migrator.migrate_mongo_course(course_key, user, org, course, run)
