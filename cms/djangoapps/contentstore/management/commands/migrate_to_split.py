# pylint: disable=protected-access

"""
Django management command to migrate a course from the old Mongo modulestore
to the new split-Mongo modulestore.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.split_migrator import SplitMigrator
from xmodule.modulestore.django import loc_mapper
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore import ModuleStoreEnum


def user_from_str(identifier):
    """
    Return a user identified by the given string. The string could be an email
    address, or a stringified integer corresponding to the ID of the user in
    the database. If no user could be found, a User.DoesNotExist exception
    will be raised.
    """
    try:
        user_id = int(identifier)
    except ValueError:
        return User.objects.get(email=identifier)
    else:
        return User.objects.get(id=user_id)


class Command(BaseCommand):
    "Migrate a course from old-Mongo to split-Mongo"

    help = "Migrate a course from old-Mongo to split-Mongo"
    args = "course_key email <new org> <new offering>"

    def parse_args(self, *args):
        """
        Return a 4-tuple of (course_key, user, org, offering).
        If the user didn't specify an org & offering, those will be None.
        """
        if len(args) < 2:
            raise CommandError(
                "migrate_to_split requires at least two arguments: "
                "a course_key and a user identifier (email or ID)"
            )

        try:
            course_key = CourseKey.from_string(args[0])
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(args[0])

        try:
            user = user_from_str(args[1])
        except User.DoesNotExist:
            raise CommandError("No user found identified by {}".format(args[1]))

        try:
            org = args[2]
            offering = args[3]
        except IndexError:
            org = offering = None

        return course_key, user, org, offering

    def handle(self, *args, **options):
        course_key, user, org, offering = self.parse_args(*args)

        migrator = SplitMigrator(
            draft_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo),
            split_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split),
            loc_mapper=loc_mapper(),
        )

        migrator.migrate_mongo_course(course_key, user, org, offering)
