"""
Django management command to generate a test course in a specific modulestore
"""
import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from contentstore.management.commands.utils import user_from_str
from contentstore.views.course import create_new_course_in_store
from xmodule.modulestore import ModuleStoreEnum
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Command(BaseCommand):
    """ Generate a basic course """
    help = 'Generate a course with settings on studio'

    def add_arguments(self, parser):
        parser.add_argument(
            'json',
            help='JSON object with values for store, user, name, organization, number, fields'
        )

    def handle(self, *args, **options):

        if options["json"] is None:
            raise CommandError("Must pass in JSON object")

        try:
            settings = json.loads(options["json"])
        except ValueError:
            raise CommandError("Invalid JSON")

        if not(all(key in settings for key in ("store", "user", "organization", "number", "run", "fields"))):
            raise CommandError("JSON object is missing required fields")

        if settings["store"] in [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split]:
            store = settings["store"]
        else:
            raise CommandError("Modulestore invalid_store is not valid")

        try:
            user = user_from_str(settings["user"])
        except User.DoesNotExist:
            raise CommandError("User {user} not found".format(user=settings["user"]))

        org = settings["organization"]
        num = settings["number"]
        run = settings["run"]
        fields = settings["fields"]

        # Create the course
        new_course = create_new_course_in_store(store, user, org, num, run, fields)
        self.stdout.write(u"Created {}".format(unicode(new_course.id)))
