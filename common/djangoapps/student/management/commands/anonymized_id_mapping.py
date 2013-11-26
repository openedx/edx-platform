# -*- coding: utf-8 -*-
"""Dump username,unique_id_for_user pairs as CSV.

Give instructors easy access to the mapping from anonymized IDs to user IDs
with a simple Django management command to generate a CSV mapping. To run, use
the following:

rake django-admin[anonymized_id_mapping,x,y,z]

[Naturally, substitute the appropriate values for x, y, and z. (I.e.,
 lms, dev, and MITx/6.002x/Circuits)]"""

import csv

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from student.models import unique_id_for_user


class Command(BaseCommand):
    """Add our handler to the space where django-admin looks up commands."""

    # It appears that with the way Rake invokes these commands, we can't
    # have more than one arg passed through...annoying.
    args = ("course_id", )

    help = """Export a CSV mapping usernames to anonymized ids

    Exports a CSV document mapping each username in the specified course to
    the anonymized, unique user ID.
    """

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Usage: unique_id_mapping %s" %
                               " ".join(("<%s>" % arg for arg in Command.args)))

        course_id = args[0]

        # Generate the output filename from the course ID.
        # Change slashes to dashes first, and then append .csv extension.
        output_filename = course_id.replace('/', '-') + ".csv"

        # Figure out which students are enrolled in the course
        students = User.objects.filter(courseenrollment__course_id=course_id)
        if len(students) == 0:
            self.stdout.write("No students enrolled in %s" % course_id)
            return

        # Write mapping to output file in CSV format with a simple header
        try:
            with open(output_filename, 'wb') as output_file:
                csv_writer = csv.writer(output_file)
                csv_writer.writerow(("User ID", "Anonymized user ID"))
                for student in students:
                    csv_writer.writerow((student.id, unique_id_for_user(student)))
        except IOError:
            raise CommandError("Error writing to file: %s" % output_filename)

