import os.path

from optparse import make_option

from django.utils.html import escape
from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore

from licenses.models import Software, StudentLicense


class Command(BaseCommand):
    help = """Imports serial numbers for software used in a course.

    Usage: import_serials course_id software_id serial_file

    serial_file is a text file that list one available serial number per line.

    Example:
      import_serials.py MITx/6.002x/2012_Fall matlab /tmp/matlab-serials.txt
    """

    args = "course_id software_id serial_file"

    def handle(self, *args, **options):
        """
        """
        course_id, software_name, filename = self._parse_arguments(args)

        software = self._find_software(course_id, software_name)

        self._import_serials(software, filename)

    def _parse_arguments(self, args):
        if len(args) != 3:
            raise CommandError("Incorrect number of arguments")

        course_id = args[0]
        courses = modulestore().get_courses()
        known_course_ids = set(c.id for c in courses)

        if course_id not in known_course_ids:
            raise CommandError("Unknown course_id")

        software_name = escape(args[1].lower())

        filename = os.path.abspath(args[2])
        if not os.path.exists(filename):
            raise CommandError("Cannot find filename {0}".format(filename))

        return course_id, software_name, filename

    def _find_software(self, course_id, software_name):
        try:
            software = Software.objects.get(course_id=course_id, name=software_name)
        except Software.DoesNotExist:
            software = Software(name=software_name, course_id=course_id)
            software.save()

        return software

    def _import_serials(self, software, filename):
        print "Importing serial numbers for {0} {1}".format(
            software.name, software.course_id)

        known_serials = set(l.serial for l in  StudentLicense.objects.filter(software=software))

        count = 0
        serials = list(l.strip() for l in open(filename))
        for s in serials:
            if s not in known_serials:
                license = StudentLicense(software=software, serial=s)
                license.save()
                count += 1

        print "{0} new serial numbers imported.".format(count)
