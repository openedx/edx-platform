"""
======== Populate StudentModuleExpand  ===============================================================================

Populates the StudentModuleExpand table of the queryable_table model.

For the provided course_id, it will find all rows in the StudentModule table of the courseware model that have
module_type 'problem' and the grade is not null. Then for any rows that have changed since the last populate or do not
have a corresponding row, update the attempts value.
"""

import json

from django.core.management.base import BaseCommand

from courseware.models import StudentModule
from queryable_student_module.models import Log, StudentModuleExpand
from queryable_student_module.util import pre_run_command, more_options
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata


class Command(BaseCommand):
    """
    populate_studentmoduleexpand command
    """

    help = "Populates the queryable.StudentModuleExpand table.\n"
    help += "Usage: populate_studentmoduleexpand course_id\n"
    help += "   course_id: course's ID, such as Medicine/HRP258/Statistics_in_Medicine\n"

    option_list = BaseCommand.option_list + (more_options(),)

    def handle(self, *args, **options):
        script_id = "studentmoduleexpand"

        print "args = ", args

        if len(args) > 0:
            course_id = args[0]
        else:
            print self.help
            return

        iterative_populate, tstart, last_log_run = pre_run_command(script_id, options, course_id)

        # If iterative populate, get all the problems that students have submitted an answer to for this course,
        # since the last run
        if iterative_populate:
            sm_rows = StudentModule.objects.select_related('student', 'student__profile').filter(course_id__exact=course_id, grade__isnull=False,
                                                   module_type__exact="problem", modified__gte=last_log_run[0].created)
        else:
            sm_rows = StudentModule.objects.select_related('student', 'student__profile').filter(course_id__exact=course_id, grade__isnull=False,
                                                   module_type__exact="problem")

        c_updated_rows = 0
        # For each problem, get or create the corresponding StudentModuleExpand row
        for sm_row in sm_rows:
            
            # Get the display name for the problem
            module_state_key = sm_row.module_state_key
            problem = modulestore().get_instance(course_id, module_state_key, 0)
            problem_name = own_metadata(problem)['display_name']

            sme, created = StudentModuleExpand.objects.get_or_create(student_id=sm_row.student_id, course_id=course_id,
                                                                     module_state_key=module_state_key,
                                                                     student_module_id=sm_row.id)

            # If the StudentModuleExpand row is new or the StudentModule row was
            # more recently updated than the StudentModuleExpand row, fill in/update
            # everything and save
            if created or (sme.modified < sm_row.modified):
                c_updated_rows += 1
                sme.grade = sm_row.grade
                sme.max_grade = sm_row.max_grade
                state = json.loads(sm_row.state)
                sme.attempts = state["attempts"]
                sme.label = problem_name
                sme.username = sm_row.student.username
                sme.name = sm_row.student.profile.name
                sme.save()

        c_all_rows = len(sm_rows)
        print "--------------------------------------------------------------------------------"
        print "Done! Updated/Created {0} queryable rows out of {1} from courseware_studentmodule".format(
            c_updated_rows, c_all_rows)
        print "--------------------------------------------------------------------------------"

        # Save since everything finished successfully, log latest run.
        q_log = Log(script_id=script_id, course_id=course_id, created=tstart)
        q_log.save()
