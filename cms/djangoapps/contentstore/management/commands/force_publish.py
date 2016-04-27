"""
Script for force publishing a course
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from .prompt import query_yes_no
from .utils import get_course_versions

# To run from command line: ./manage.py cms force_publish course-v1:org+course+run


class Command(BaseCommand):
    """Force publish a course"""
    help = '''
    Force publish a course. Takes two arguments:
    <course_id>: the course id of the course you want to publish forcefully
    commit: do the force publish

    If you do not specify 'commit', the command will print out what changes would be made.
    '''

    def handle(self, *args, **options):
        """Execute the command"""
        if len(args) not in {1, 2}:
            raise CommandError("force_publish requires 1 or more argument: <course_id> |commit|")

        try:
            course_key = CourseKey.from_string(args[0])
        except InvalidKeyError:
            raise CommandError("Invalid course key.")

        if not modulestore().get_course(course_key):
            raise CommandError("Course not found.")

        commit = False
        if len(args) == 2:
            commit = args[1] == 'commit'

        # for now only support on split mongo
        owning_store = modulestore()._get_modulestore_for_courselike(course_key)  # pylint: disable=protected-access
        if hasattr(owning_store, 'force_publish_course'):
            versions = get_course_versions(args[0])
            print "Course versions : {0}".format(versions)

            if commit:
                if query_yes_no("Are you sure to publish the {0} course forcefully?".format(course_key), default="no"):
                    # publish course forcefully
                    updated_versions = owning_store.force_publish_course(
                        course_key, ModuleStoreEnum.UserID.mgmt_command, commit
                    )
                    if updated_versions:
                        # if publish and draft were different
                        if versions['published-branch'] != versions['draft-branch']:
                            print "Success! Published the course '{0}' forcefully.".format(course_key)
                            print "Updated course versions : \n{0}".format(updated_versions)
                        else:
                            print "Course '{0}' is already in published state.".format(course_key)
                    else:
                        print "Error! Could not publish course {0}.".format(course_key)
            else:
                # if publish and draft were different
                if versions['published-branch'] != versions['draft-branch']:
                    print "Dry run. Following would have been changed : "
                    print "Published branch version {0} changed to draft branch version {1}".format(
                        versions['published-branch'], versions['draft-branch']
                    )
                else:
                    print "Dry run. Course '{0}' is already in published state.".format(course_key)
        else:
            raise CommandError("The owning modulestore does not support this command.")
