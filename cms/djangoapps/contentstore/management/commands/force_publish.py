"""
Script for force publishing a course
"""


from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from .prompt import query_yes_no
from .utils import get_course_versions

# To run from command line: ./manage.py cms force_publish course-v1:org+course+run


class Command(BaseCommand):
    """Force publish a course"""
    help = '''
    Force publish a course. Takes two arguments:
    <course_id>: the course id of the course you want to publish forcefully
    --commit: do the force publish

    If you do not specify '--commit', the command will print out what changes would be made.
    '''

    def add_arguments(self, parser):
        parser.add_argument('course_key', help="ID of the Course to force publish")
        parser.add_argument('--commit', action='store_true', help="Pull updated metadata from external IDPs")

    def handle(self, *args, **options):
        """Execute the command"""

        try:
            course_key = CourseKey.from_string(options['course_key'])
        except InvalidKeyError:
            raise CommandError("Invalid course key.")

        if not modulestore().get_course(course_key):
            raise CommandError("Course not found.")

        # for now only support on split mongo
        owning_store = modulestore()._get_modulestore_for_courselike(course_key)  # pylint: disable=protected-access
        if hasattr(owning_store, 'force_publish_course'):
            versions = get_course_versions(options['course_key'])
            print(u"Course versions : {0}".format(versions))

            if options['commit']:
                if query_yes_no(u"Are you sure to publish the {0} course forcefully?".format(course_key), default="no"):
                    # publish course forcefully
                    updated_versions = owning_store.force_publish_course(
                        course_key, ModuleStoreEnum.UserID.mgmt_command, options['commit']
                    )
                    if updated_versions:
                        # if publish and draft were different
                        if versions['published-branch'] != versions['draft-branch']:
                            print(u"Success! Published the course '{0}' forcefully.".format(course_key))
                            print(u"Updated course versions : \n{0}".format(updated_versions))
                        else:
                            print(u"Course '{0}' is already in published state.".format(course_key))
                    else:
                        print(u"Error! Could not publish course {0}.".format(course_key))
            else:
                # if publish and draft were different
                if versions['published-branch'] != versions['draft-branch']:
                    print("Dry run. Following would have been changed : ")
                    print(u"Published branch version {0} changed to draft branch version {1}".format(
                        versions['published-branch'], versions['draft-branch'])
                    )
                else:
                    print(u"Dry run. Course '{0}' is already in published state.".format(course_key))
        else:
            raise CommandError("The owning modulestore does not support this command.")
