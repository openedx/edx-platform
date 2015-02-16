#!/usr/bin/python
"""
django management command: dump grades to csv files
for use by batch processes
"""
import csv

from instructor.views.legacy import get_student_grade_summary_data
from courseware.courses import get_course_by_id
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from django.core.management.base import BaseCommand
from instructor.utils import DummyRequest


class Command(BaseCommand):
    help = "dump grades to CSV file.  Usage: dump_grades course_id_or_dir filename dump_type\n"
    help += "   course_id_or_dir: either course_id or course_dir\n"
    help += "   filename: where the output CSV is to be stored\n"
    # help += "   start_date: end date as M/D/Y H:M (defaults to end of available data)"
    help += "   dump_type: 'all' or 'raw' (see instructor dashboard)"

    def handle(self, *args, **options):

        # current grading logic and data schema doesn't handle dates
        # datetime.strptime("21/11/06 16:30", "%m/%d/%y %H:%M")

        print "args = ", args

        course_id = 'MITx/8.01rq_MW/Classical_Mechanics_Reading_Questions_Fall_2012_MW_Section'
        fn = "grades.csv"
        get_raw_scores = False

        if len(args) > 0:
            course_id = args[0]
        if len(args) > 1:
            fn = args[1]
        if len(args) > 2:
            get_raw_scores = args[2].lower() == 'raw'

        request = DummyRequest()
        # parse out the course into a coursekey
        try:
            course_key = CourseKey.from_string(course_id)
        # if it's not a new-style course key, parse it from an old-style
        # course key
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        try:
            course = get_course_by_id(course_key)
        # Ok with catching general exception here because this is run as a management command
        # and the exception is exposed right away to the user.
        except Exception as err:  # pylint: disable=broad-except
            print "-----------------------------------------------------------------------------"
            print "Sorry, cannot find course with id {}".format(course_id)
            print "Got exception {}".format(err)
            print "Please provide a course ID or course data directory name, eg content-mit-801rq"
            return

        print "-----------------------------------------------------------------------------"
        print "Dumping grades from {} to file {} (get_raw_scores={})".format(course.id, fn, get_raw_scores)
        datatable = get_student_grade_summary_data(request, course, get_raw_scores=get_raw_scores)

        fp = open(fn, 'w')

        writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([unicode(s).encode('utf-8') for s in datatable['header']])
        for datarow in datatable['data']:
            encoded_row = [unicode(s).encode('utf-8') for s in datarow]
            writer.writerow(encoded_row)

        fp.close()
        print "Done: {} records dumped".format(len(datatable['data']))
