"""Script for deleting orphans"""
from django.core.management.base import BaseCommand, CommandError
from contentstore.views.item import _delete_orphans
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from xmodule.modulestore import ModuleStoreEnum


class Command(BaseCommand):
    """Command for deleting orphans"""
    help = '''
    Delete orphans from a MongoDB backed course. Takes two arguments:
    <course_id>: the course id of the course whose orphans you want to delete
    |commit|: optional argument. If not provided, will not run task.
    '''

    def add_arguments(self, parser):
        parser.add_argument('course_id')
        parser.add_argument('--commit', action='store')

    def handle(self, *args, **options):
        try:
            course_key = CourseKey.from_string(options['course_id'])
        except InvalidKeyError:
            raise CommandError("Invalid course key.")

        commit = False
        if options['commit']:
            commit = options['commit'] == 'commit'

        if commit:
            print 'Deleting orphans from the course:'
            deleted_items = _delete_orphans(
                course_key, ModuleStoreEnum.UserID.mgmt_command, commit
            )
            print "Success! Deleted the following orphans from the course:"
            print "\n".join(deleted_items)
        else:
            print 'Dry run. The following orphans would have been deleted from the course:'
            deleted_items = _delete_orphans(
                course_key, ModuleStoreEnum.UserID.mgmt_command, commit
            )
            print "\n".join(deleted_items)
