"""
Django management command to rollback a migration to split. The way to do this
is to delete the course from the split mongo datastore.
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.locator import CourseLocator


class Command(BaseCommand):
    "Delete a course from the split Mongo datastore"

    help = "Delete a course from the split Mongo datastore"
    args = "locator"

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError(
                "delete_split_course requires at least one argument (locator)"
            )

        try:
            locator = CourseLocator(url=args[0])
        except ValueError:
            raise CommandError("Invalid locator string {}".format(args[0]))

        try:
            modulestore('split').delete_course(locator.package_id)
        except ItemNotFoundError:
            raise CommandError("No course found with locator {}".format(locator))
