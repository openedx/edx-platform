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
    args = "modulestore user org course run"

    def parse_args(self, *args):
        """
        Return a tuple of passed in values for (modulestore, user, org, course, run).
        """
        if len(args) != 5:
            raise CommandError(
                "create_course requires 5 arguments: "
                "a modulestore, user, org, course, run. Modulestore is one of {}".format(
                    [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split]
                )
            )

        if args[0] not in [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split]:
            raise CommandError(
                "Modulestore (first arg) must be one of {}".format(
                    [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split]
                )
            )
        storetype = args[0]

        try:
            user = user_from_str(args[1])
        except User.DoesNotExist:
            raise CommandError(
                "No user {user} found: expected args are {args}".format(
                    user=args[1],
                    args=self.args,
                ),
            )

        org = args[2]
        course = args[3]
        run = args[4]

        return storetype, user, org, course, run

    def handle(self, *args, **options):
        storetype, user, org, course, run = self.parse_args(*args)
        new_course = create_new_course_in_store(storetype, user, org, course, run, {})
        self.stdout.write(u"Created {}".format(unicode(new_course.id)))
