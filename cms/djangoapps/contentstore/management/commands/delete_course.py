###
### Script for cloning a course
###
from django.core.management.base import BaseCommand, CommandError
from .prompt import query_yes_no
from contentstore.utils import delete_course_and_groups


class Command(BaseCommand):
    help = '''Delete a MongoDB backed course'''

    def handle(self, *args, **options):
        if len(args) != 1 and len(args) != 2:
            raise CommandError("delete_course requires one or more arguments: <location> |commit|")

        course_id = args[0]

        commit = False
        if len(args) == 2:
            commit = args[1] == 'commit'

        if commit:
            print('Actually going to delete the course from DB....')

        if query_yes_no("Deleting course {0}. Confirm?".format(course_id), default="no"):
            if query_yes_no("Are you sure. This action cannot be undone!", default="no"):
                delete_course_and_groups(course_id, commit)
