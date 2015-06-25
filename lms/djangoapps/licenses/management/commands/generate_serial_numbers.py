from uuid import uuid4

from django.utils.html import escape
from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore

from licenses.models import CourseSoftware, UserLicense
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    help = """Generate random serial numbers for software used in a course.

    Usage: generate_serial_numbers <course_id> <software_name> <count>

    <count> is the number of numbers to generate.

    Example:

       import_serial_numbers MITx/6.002x/2012_Fall matlab 100

    """
    args = "course_id software_id count"

    def handle(self, *args, **options):
        course_id, software_name, count = self._parse_arguments(args)

        software, _ = CourseSoftware.objects.get_or_create(course_id=course_id,
                                                           name=software_name)
        self._generate_serials(software, count)

    def _parse_arguments(self, args):
        if len(args) != 3:
            raise CommandError("Incorrect number of arguments")

        course_id = args[0]
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        if not modulestore().has_course(course_key):
            raise CommandError("Unknown course_id")

        software_name = escape(args[1].lower())

        try:
            count = int(args[2])
        except ValueError:
            raise CommandError("Invalid <count> argument.")

        return course_key, software_name, count

    def _generate_serials(self, software, count):
        print "Generating {0} serials".format(count)

        # add serial numbers them to the database
        for _ in xrange(count):
            serial = str(uuid4())
            license = UserLicense(software=software, serial=serial)
            license.save()

        print "{0} new serial numbers generated.".format(count)
