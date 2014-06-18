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
    args = "course_key email <new org> <new course> <new run>"

    def parse_args(self, *args):
        """
        Return a 5-tuple of (course_key, user, org, course, run).
        If the user didn't specify an org, course, and run, those will be None.
        """
        if len(args) < 2:
            raise CommandError(
                "migrate_to_split requires at least two arguments: "
                "a course_key and a user identifier (email or ID)"
            )

        course_key = CourseKey.from_string(args[0])

        try:
            user = user_from_str(args[1])
        except User.DoesNotExist:
            raise CommandError("No user found identified by {}".format(args[1]))

        try:
            org = args[2]
            course = args[3]
            run = args[4]
        except IndexError:
            org = course = run = None

        return course_key, user, org, course, run

    def handle(self, *args, **options):
        course_key, user, org, course, run = self.parse_args(*args)

        migrator = SplitMigrator(
            draft_modulestore=modulestore('default'),
            direct_modulestore=modulestore('direct'),
            split_modulestore=modulestore('split'),
            loc_mapper=loc_mapper(),
        )

        migrator.migrate_mongo_course(course_key, user, org, course, run)
