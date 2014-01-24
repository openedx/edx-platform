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


class Command(BaseCommand):
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

        try:
            location = Location(args[0])
        except InvalidLocationError:
            raise CommandError("Invalid location string {}".format(args[0]))

        user_id = None
        email = None
        try:
            user_id = int(args[1])
        except ValueError:
            email = args[1]
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise CommandError("No user exists with ID {}".format(user_id))
        else:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise CommandError("No user exists with email {}".format(email))

        assert user, "User doesn't exist! That shouldn't happen..."

        try:
            locator_string = args[2]
        except IndexError:
            locator_string = None

        return location, user, locator_string

    def handle(self, *args, **options):
        location, user, locator_string = self.parse_args(*args)

        draft = modulestore('default')
        direct = modulestore('direct')
        split = modulestore('split')

        migrator = SplitMigrator(
            draft_modulestore=draft,
            direct_modulestore=direct,
            split_modulestore=split,
            loc_mapper=split.loc_mapper,
        )

        migrator.migrate_mongo_course(location, user, locator_string)
