"""
Django management command to create a course in a specific modulestore
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from xmodule.modulestore import ModuleStoreEnum
from contentstore.views.course import create_new_course_in_store
from contentstore.management.commands.utils import user_from_str


class Command(BaseCommand):
    """
    Create a course in a specific modulestore.
    """

    # can this query modulestore for the list of write accessible stores or does that violate command pattern?
    help = "Create a course in one of {}".format([ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split])

    def add_arguments(self, parser):
        parser.add_argument('modulestore')
        parser.add_argument('user')
        parser.add_argument('org')
        parser.add_argument('course')
        parser.add_argument('run')

    def handle(self, *args, **options):
        if options['modulestore'] not in [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split]:
            raise CommandError(
                "modulestore must be one of {}".format(
                    [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split]
                )
            )
        storetype = options['modulestore']

        try:
            user = user_from_str(options['user'])
        except User.DoesNotExist:
            raise CommandError(
                "No user {user} found".format(user=options['user'])
            )

        org = options['org']
        course = options['course']
        run = options['run']

        new_course = create_new_course_in_store(storetype, user, org, course, run, {})
        self.stdout.write(u"Created {}".format(unicode(new_course.id)))
