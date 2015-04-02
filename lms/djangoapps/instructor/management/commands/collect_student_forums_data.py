"""
Command to retrieve aggregated student forums data in a .csv
"""
import csv
import optparse
import os

from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from instructor.utils import collect_student_forums_data


class Command(BaseCommand):
    """
    Retrieve aggregated student forums data, write to .csv
    """

    help = ('Usage: collect_course_forums_data <course_id> --output-dir=<output_dir>')
    args = '<course_id>'
    option_list = BaseCommand.option_list + (
        optparse.make_option('-o', '--output-dir',
        action='store', dest='output_dir', default=None,
        help='Write output to a directory rather than stdout'),
    )

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Course ID must be specified to fetch data')

        try:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(args[0])
        except InvalidKeyError:
            raise CommandError('The course ID given was invalid')

        file_name = "{course_id}-student-forums.csv".format(course_id=args[0].replace("/", "-"))

        if options['output_dir']:
            csv_file = open(os.path.join(options['output_dir'], file_name), 'wb')
        else:
            csv_file = self.stdout

        writer = csv.writer(csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)

        header, rows = collect_student_forums_data(course_id)

        writer.writerow(header)
        for row in rows:
            writer.writerow(_utf8_encoded_row(row))


def _utf8_encoded_row(row):
    """Encodes a row to utf-8"""
    return [unicode(item).encode('utf-8') for item in row]
