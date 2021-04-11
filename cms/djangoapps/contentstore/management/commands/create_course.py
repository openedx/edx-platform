"""
Django management command to create a course in a specific modulestore
"""


from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from six import text_type

from cms.djangoapps.contentstore.management.commands.utils import user_from_str
from cms.djangoapps.contentstore.views.course import create_new_course_in_store
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import DuplicateCourseError

MODULESTORE_CHOICES = (ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)


class Command(BaseCommand):
    """
    Create a course in a specific modulestore.
    """

    # can this query modulestore for the list of write accessible stores or does that violate command pattern?
    help = u"Create a course in one of {}".format([ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split])

    def add_arguments(self, parser):
        parser.add_argument('modulestore',
                            choices=MODULESTORE_CHOICES,
                            help=u"Modulestore must be one of {}".format(MODULESTORE_CHOICES))
        parser.add_argument('user',
                            help="The instructor's email address or integer ID.")
        parser.add_argument('org',
                            help="The organization to create the course within.")
        parser.add_argument('number',
                            help="The number of the course.")
        parser.add_argument('run',
                            help="The name of the course run.")
        parser.add_argument('name',
                            nargs='?',
                            default=None,
                            help="The display name of the course. (OPTIONAL)")
        parser.add_argument('start_date',
                            nargs='?',
                            default=None,
                            help="The start date of the course. Format: YYYY-MM-DD")

    def get_user(self, user):
        """
        Return a User object.
        """
        try:
            user_object = user_from_str(user)
        except User.DoesNotExist:
            raise CommandError(u"No user {user} found.".format(user=user))
        return user_object

    def handle(self, *args, **options):

        run = options['run']
        org = options['org']
        name = options['name']
        number = options['number']
        storetype = options['modulestore']
        start_date = options["start_date"]
        user = self.get_user(options['user'])

        # start date is set one week ago if not given
        start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now() - timedelta(days=7)

        if storetype == ModuleStoreEnum.Type.mongo:
            self.stderr.write("WARNING: The 'Old Mongo' store is deprecated. New courses should be added to split.")

        fields = {
            "start": start_date
        }
        if name:
            fields["display_name"] = name

        try:
            new_course = create_new_course_in_store(
                storetype,
                user,
                org,
                number,
                run,
                fields
            )
            self.stdout.write(u"Created {}".format(text_type(new_course.id)))
        except DuplicateCourseError:
            self.stdout.write(u"Course already exists")
