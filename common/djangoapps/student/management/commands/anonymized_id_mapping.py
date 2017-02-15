# -*- coding: utf-8 -*-
"""Dump username, per-student anonymous id, and per-course anonymous id triples as CSV.

Give instructors easy access to the mapping from anonymized IDs to user IDs
with a simple Django management command to generate a CSV mapping. To run, use
the following:

./manage.py lms anonymized_id_mapping COURSE_ID
"""

import csv

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from student.models import anonymous_id_for_user
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    """Add our handler to the space where django-admin looks up commands."""

    # TODO: revisit now that rake has been deprecated
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

        course_key = SlashSeparatedCourseKey.from_deprecated_string(args[0])

        # Generate the output filename from the course ID.
        # Change slashes to dashes first, and then append .csv extension.
        output_filename = course_key.to_deprecated_string().replace('/', '-') + ".csv"

        # Figure out which students are enrolled in the course
        students = User.objects.filter(courseenrollment__course_id=course_key)
        if len(students) == 0:
            self.stdout.write("No students enrolled in %s" % course_key.to_deprecated_string())
            return

        # Write mapping to output file in CSV format with a simple header
        try:
            with open(output_filename, 'wb') as output_file:
                csv_writer = csv.writer(output_file)
                csv_writer.writerow((
                    "User ID",
                    "Per-Student anonymized user ID",
                    "Per-course anonymized user id"
                ))
                for student in students:
                    csv_writer.writerow((
                        student.id,
                        anonymous_id_for_user(student, None),
                        anonymous_id_for_user(student, course_key)
                    ))
        except IOError:
            raise CommandError("Error writing to file: %s" % output_filename)
