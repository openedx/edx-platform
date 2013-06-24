#!/usr/bin/python
#
# django management command: dump grades to csv files
# for use by batch processes

from instructor.offline_gradecalc import offline_grade_calculation
from courseware.courses import get_course_by_id
from xmodule.modulestore.django import modulestore

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compute grades for all students in a course, and store result in DB.\n"
    help += "Usage: compute_grades course_id_or_dir \n"
    help += "   course_id_or_dir: either course_id or course_dir\n"
    help += 'Example course_id: MITx/8.01rq_MW/Classical_Mechanics_Reading_Questions_Fall_2012_MW_Section'

    def handle(self, *args, **options):

        print "args = ", args

        if len(args) > 0:
            course_id = args[0]
        else:
            print self.help
            return

        try:
            course = get_course_by_id(course_id)
        except Exception as err:
            if course_id in modulestore().courses:
                course = modulestore().courses[course_id]
            else:
                print "-----------------------------------------------------------------------------"
                print "Sorry, cannot find course %s" % course_id
                print "Please provide a course ID or course data directory name, eg content-mit-801rq"
                return

        print "-----------------------------------------------------------------------------"
        print "Computing grades for %s" % (course.id)

        offline_grade_calculation(course.id)
