import os.path

from django.utils.html import escape
from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore

from licenses.models import CourseSoftware, UserLicense
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    help = """Imports serial numbers for software used in a course.

    Usage: import_serial_numbers <course_id> <software_name> <file>

    <file> is a text file that list one available serial number per line.

    Example:

       import_serial_numbers MITx/6.002x/2012_Fall matlab serials.txt

    """
    args = "course_id software_id serial_file"

    def handle(self, *args, **options):
        course_id, software_name, filename = self._parse_arguments(args)

        software, _ = CourseSoftware.objects.get_or_create(course_id=course_id,
                                                           name=software_name)
        self._import_serials(software, filename)

    def _parse_arguments(self, args):
        if len(args) != 3:
            raise CommandError("Incorrect number of arguments")

        course_id = args[0]
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        if not modulestore().has_course(course_key):
            raise CommandError("Unknown course_id")

        software_name = escape(args[1].lower())

        filename = os.path.abspath(args[2])
        if not os.path.exists(filename):
            raise CommandError("Cannot find filename {0}".format(filename))

        return course_key, software_name, filename

    def _import_serials(self, software, filename):
        print "Importing serial numbers for {0}.".format(software)

        serials = set(unicode(l.strip()) for l in open(filename))

        # remove serial numbers we already have
        licenses = UserLicense.objects.filter(software=software)
        known_serials = set(l.serial for l in licenses)
        if known_serials:
            serials = serials.difference(known_serials)

        # add serial numbers them to the database
        for serial in serials:
            license = UserLicense(software=software, serial=serial)
            license.save()

        print "{0} new serial numbers imported.".format(len(serials))
