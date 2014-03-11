"""
Django management command to migrate a course from the old Mongo modulestore
to the new split-Mongo modulestore.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.split_migrator import SplitMigrator
from xmodule.modulestore import InvalidLocationError
from xmodule.modulestore.django import loc_mapper


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
    args = "location email <locator>"

    def parse_args(self, *args):
        """
        Return a three-tuple of (location, user, locator_string).
        If the user didn't specify a locator string, the third return value
        will be None.
        """
        if len(args) < 2:
            raise CommandError(
                "migrate_to_split requires at least two arguments: "
                "a location and a user identifier (email or ID)"
            )

        location = args[0]

        try:
            user = user_from_str(args[1])
        except User.DoesNotExist:
            raise CommandError("No user found identified by {}".format(args[1]))

        try:
            package_id = args[2]
        except IndexError:
            package_id = None

        return location, user, package_id

    def handle(self, *args, **options):
        location, user, package_id = self.parse_args(*args)

        migrator = SplitMigrator(
            draft_modulestore=modulestore('default'),
            direct_modulestore=modulestore('direct'),
            split_modulestore=modulestore('split'),
            loc_mapper=loc_mapper(),
        )

        migrator.migrate_mongo_course(location, user, package_id)
