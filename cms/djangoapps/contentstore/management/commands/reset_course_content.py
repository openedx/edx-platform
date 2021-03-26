"""
Django management command to reset the content of a course to a a different
version, as specified by an ObjectId from the DraftVersioningModulestore (aka Split).
"""
from textwrap import dedent

from django.core.management import BaseCommand, CommandError
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Reset the content of a course run to a different version, and publish.

    This is a powerful command; use with care.
    It's analogous to `git reset --hard VERSION && git push -f`.

    The intent of this is to restore overwritten course content that has not yet been
    pruned from the modulestore. I guess you could use it to change a course's content
    to any structure in Split you wanted, though.

    Make sure you have validated the value of `course_id` and `version_guid`.
    There is no confirmation prompt.

    Example:

        ./manage.py reset_course_content "course-v1:my+cool+course" "5fb5772e2fe4c7c76493c241"
    """
    help = dedent(__doc__)

    def add_arguments(self, parser):
        parser.add_argument(
            'course_id',
            help="A split-modulestore course key string (ie, course-v1:ORG+COURSE+RUN)",
        )
        parser.add_argument(
            'version_guid',
            help="A split-modulestore structure ObjectId (a 24-digit hex string)",
        )

    def handle(self, *args, **options):
        course_key = CourseKey.from_string(options["course_id"])

        version_guid = options["version_guid"]
        unparseable_guid = False
        try:
            int(version_guid, 16)
        except ValueError:
            unparseable_guid = True
        if unparseable_guid or len(version_guid) != 24:
            raise CommandError("version_guid should be a 24-digit hexadecimal number")

        print(f"Resetting '{course_key}' to version '{version_guid}'...")
        modulestore().reset_course_to_version(
            course_key,
            version_guid,
            ModuleStoreEnum.UserID.mgmt_command,
        )
        print("Done.")
