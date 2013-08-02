# ======== Populate StudentModuleExpand  ===============================================================================
#
# Populates the StudentModuleExpand table of the queryable_table model.
#
# For the provided course_id, it will find all rows in the StudentModule table of the courseware model that have
# module_type 'problem' and the grade is not null. Then for any rows that have changed since the last populate or do not
# have a corresponding row, update the attempts value.

import json

from datetime import datetime
from pytz import UTC
from optparse import make_option
from django.core.management.base import BaseCommand

from xmodule.modulestore.django import modulestore

from courseware.models import StudentModule
from queryable.models import Log
from queryable.models import StudentModuleExpand

class Command(BaseCommand):
    help = "Populates the queryable.StudentModuleExpand table.\n"
    help += "Usage: populate_studentmoduleexpand course_id\n"
    help += "   course_id: course's ID, such as Medicine/HRP258/Statistics_in_Medicine\n"

    option_list = BaseCommand.option_list + (
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help='Forces a full populate for all students and rows, rather than iterative.'),
        )

    def handle(self, *args, **options):
        script_id = "studentmoduleexpand"

        print "args = ", args

        if len(args) > 0:
            course_id = args[0]
        else:
            print self.help
            return

        print "--------------------------------------------------------------------------------"
        print "Populating queryable.StudentModuleExpand table for course {0}".format(course_id)
        print "--------------------------------------------------------------------------------"

        # Grab when we start, to log later
        tstart = datetime.now(UTC)

        iterative_populate = True
        if options['force']:
            print "--------------------------------------------------------------------------------"
            print "Full populate: Forced full populate"
            print "--------------------------------------------------------------------------------"
            iterative_populate = False

        if iterative_populate:
            # Get when this script was last run for this course
            last_log_run = Log.objects.filter(script_id__exact=script_id, course_id__exact=course_id)

            length = len(last_log_run)
            print "--------------------------------------------------------------------------------"
            if length > 0:
                print "Iterative populate: Last log run", last_log_run[0].created
            else:
                print "Full populate: Can't find log of last run"
                iterative_populate = False
            print "--------------------------------------------------------------------------------"
        
        # If iterative populate, get all the problems that students have submitted an answer to for this course,
        # since the last run
        if iterative_populate:
            sm_rows = StudentModule.objects.filter(course_id__exact=course_id, grade__isnull=False,
                                                  module_type__exact="problem", modified__gte=last_log_run[0].created)
        else:
            sm_rows = StudentModule.objects.filter(course_id__exact=course_id, grade__isnull=False,
                                                  module_type__exact="problem")

        c_updated_rows = 0
        # For each problem, get or create the corresponding StudentModuleExpand row
        for sm in sm_rows:
            sme, created = StudentModuleExpand.objects.get_or_create(student=sm.student, course_id=course_id,
                                                                     module_state_key=sm.module_state_key,
                                                                     student_module=sm)

            # If the StudentModuleExpand row is new or the StudentModule row was
            # more recently updated than the StudentModuleExpand row, fill in/update
            # everything and save
            if created or (sme.modified < sm.modified):
                c_updated_rows += 1
                sme.grade = sm.grade
                sme.max_grade = sm.max_grade
                state = json.loads(sm.state)
                sme.attempts = state["attempts"]
                sme.save()

        c_all_rows = len(sm_rows)
        print "--------------------------------------------------------------------------------"
        print "Done! Updated/Created {0} queryable rows out of {1} from courseware_studentmodule".format(
            c_updated_rows, c_all_rows)
        print "--------------------------------------------------------------------------------"

        # Save since everything finished successfully, log latest run.
        q_log = Log(script_id=script_id, course_id=course_id, created=tstart)
        q_log.save()
