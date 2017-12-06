"""
Django management command to create a course in a specific modulestore
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from six import text_type

from contentstore.management.commands.utils import user_from_str
from contentstore.views.course import create_new_course_in_store
from xmodule.modulestore import ModuleStoreEnum

MODULESTORE_CHOICES = (ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)


class Command(BaseCommand):
    """
    Create a course in a specific modulestore.
    """

    # can this query modulestore for the list of write accessible stores or does that violate command pattern?
    help = "Create a course in one of {}".format([ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split])

    def add_arguments(self, parser):
        parser.add_argument('modulestore',
                            choices=MODULESTORE_CHOICES,
                            help="Modulestore must be one of {}".format(MODULESTORE_CHOICES))
        parser.add_argument('user',
                            help="The instructor's email address or integer ID.")
        parser.add_argument('org',
                            help="The organization to create the course within.")
        parser.add_argument('course',
                            help="The name of the course.")
        parser.add_argument('run',
                            help="The name of the course run.")

    def parse_args(self, **options):
        """
        Return a tuple of passed in values for (modulestore, user, org, course, run).
        """
        try:
            user = user_from_str(options['user'])
        except User.DoesNotExist:
            raise CommandError("No user {user} found.".format(user=options['user']))

        return options['modulestore'], user, options['org'], options['course'], options['run']

    def handle(self, *args, **options):
        storetype, user, org, course, run = self.parse_args(**options)

        if storetype == ModuleStoreEnum.Type.mongo:
            self.stderr.write("WARNING: The 'Old Mongo' store is deprecated. New courses should be added to split.")

        new_course = create_new_course_in_store(storetype, user, org, course, run, {})
        self.stdout.write(u"Created {}".format(text_type(new_course.id)))
