"""
Django management command to migrate a course from the old Mongo modulestore
to the new split-Mongo modulestore.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.split_migrator import SplitMigrator
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from xmodule.modulestore import ModuleStoreEnum
from contentstore.management.commands.utils import user_from_str


class Command(BaseCommand):
    """
    Migrate a course from old-Mongo to split-Mongo. It reuses the old course id except where overridden.
    """

    help = "Migrate a course from old-Mongo to split-Mongo. The new org, course, and run will default to the old one unless overridden"
    args = "course_key email <new org> <new course> <new run>"

    def parse_args(self, *args):
        """
        Return a 5-tuple of passed in values for (course_key, user, org, course, run).
        """
        if len(args) < 2:
            raise CommandError(
                "migrate_to_split requires at least two arguments: "
                "a course_key and a user identifier (email or ID)"
            )

        try:
            course_key = CourseKey.from_string(args[0])
        except InvalidKeyError:
            raise CommandError("Invalid location string")

        try:
            user = user_from_str(args[1])
        except User.DoesNotExist:
            raise CommandError("No user found identified by {}".format(args[1]))

        org = course = run = None
        try:
            org = args[2]
            course = args[3]
            run = args[4]
        except IndexError:
            pass

        return course_key, user.id, org, course, run

    def handle(self, *args, **options):
        course_key, user, org, course, run = self.parse_args(*args)

        migrator = SplitMigrator(
            source_modulestore=modulestore(),
            split_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split),
        )

        migrator.migrate_mongo_course(course_key, user, org, course, run)
