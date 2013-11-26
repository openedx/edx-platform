#!/usr/bin/python
#
# django management command: dump grades to csv files
# for use by batch processes

import csv

from instructor.views.legacy import get_student_grade_summary_data
from courseware.courses import get_course_by_id
from xmodule.modulestore.django import modulestore

from django.core.management.base import BaseCommand


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

        request = self.DummyRequest()
        try:
            course = get_course_by_id(course_id)
        except Exception:
            if course_id in modulestore().courses:
                course = modulestore().courses[course_id]
            else:
                print "-----------------------------------------------------------------------------"
                print "Sorry, cannot find course %s" % course_id
                print "Please provide a course ID or course data directory name, eg content-mit-801rq"
                return

        print "-----------------------------------------------------------------------------"
        print "Dumping grades from %s to file %s (get_raw_scores=%s)" % (course.id, fn, get_raw_scores)
        datatable = get_student_grade_summary_data(request, course, course.id, get_raw_scores=get_raw_scores)

        fp = open(fn, 'w')

        writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(datatable['header'])
        for datarow in datatable['data']:
            encoded_row = [unicode(s).encode('utf-8') for s in datarow]
            writer.writerow(encoded_row)

        fp.close()
        print "Done: %d records dumped" % len(datatable['data'])

    class DummyRequest(object):
        META = {}
        def __init__(self):
            return
        def get_host(self):
            return 'edx.mit.edu'
        def is_secure(self):
            return False
