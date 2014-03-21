"""
Django management command to rollback a migration to split. The way to do this
is to delete the course from the split mongo datastore.
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.locator import CourseLocator


class Command(BaseCommand):
    "Rollback a course that was migrated to the split Mongo datastore"

    help = "Rollback a course that was migrated to the split Mongo datastore"
    args = "org offering"

    def handle(self, *args, **options):
        if len(args) < 2:
            raise CommandError(
                "rollback_split_course requires 2 arguments (org offering)"
            )

        try:
            locator = CourseLocator(org=args[0], offering=args[1])
        except ValueError:
            raise CommandError("Invalid org or offering string {}, {}".format(*args))

        location = loc_mapper().translate_locator_to_location(locator, get_course=True)
        if not location:
            raise CommandError(
                "This course does not exist in the old Mongo store. "
                "This command is designed to rollback a course, not delete "
                "it entirely."
            )
        old_mongo_course = modulestore('direct').get_item(location)
        if not old_mongo_course:
            raise CommandError(
                "This course does not exist in the old Mongo store. "
                "This command is designed to rollback a course, not delete "
                "it entirely."
            )

        try:
            modulestore('split').delete_course(locator)
        except ItemNotFoundError:
            raise CommandError("No course found with locator {}".format(locator))

        print(
            'Course rolled back successfully. To delete this course entirely, '
            'call the "delete_course" management command.'
        )
