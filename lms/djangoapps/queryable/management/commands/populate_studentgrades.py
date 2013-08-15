# ======== Populate Student Grades  ====================================================================================
#
# Populates the student grade tables of the queryable_table model (CourseGrade, AssignmentTypeGrade, AssignmentGrade).
#
# For the provided course_id, it will find all students that may have changed their grade since the last populate. Of
# these students rows for the course grade and assignment type are created only if the student has submitted at
# least one answer to any problem in the course. Rows for assignments are only created if the student has submitted an
# answer to one of the problems in that assignment. Updates only occur if there is a change in the values the row should
# be storing. 

import json
import re

from datetime import datetime
from pytz import UTC
from optparse import make_option
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from courseware import grades
from courseware.courses import get_course_by_id
from courseware.models import StudentModule

from queryable.models import Log
from queryable.models import CourseGrade, AssignmentTypeGrade, AssignmentGrade

from queryable.util import get_assignment_to_problem_map
from queryable.util import approx_equal

class Command(BaseCommand):
    help = "Populates the queryable.StudentGrades table.\n"
    help += "Usage: populate_studentgrades course_id\n"
    help += "   course_id: course's ID, such as Medicine/HRP258/Statistics_in_Medicine\n"

    option_list = BaseCommand.option_list + (
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help='Forces a full populate for all students and rows, rather than iterative.'),
        )

    def handle(self, *args, **options):
        script_id = "studentgrades"

        print "args = ", args

        if len(args) > 0:
            course_id = args[0]
        else:
            print self.help
            return

        assignment_problems_map = get_assignment_to_problem_map(course_id)

        print "--------------------------------------------------------------------------------"
        print "Populating queryable.StudentGrades table for course {0}".format(course_id)
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
        
        # If iterative populate get all students since last populate, otherwise get all students that fit the criteria.
        # Criteria: match course_id, module_type is 'problem', grade is not null because it means they have submitted an
        # answer to a problem that might effect their grade.
        if iterative_populate:
            students = User.objects.filter(studentmodule__course_id=course_id,
                                           studentmodule__module_type='problem',
                                           studentmodule__grade__isnull=False,
                                           studentmodule__modified__gte=last_log_run[0].created).distinct()
        else:
            students = User.objects.filter(studentmodule__course_id=course_id,
                                           studentmodule__module_type='problem',
                                           studentmodule__grade__isnull=False).distinct()

        # Create a dummy request to pass to the grade function.
        # Code originally from lms/djangoapps/instructor/offline_gradecalc.py
        # Copying instead of using that code so everything is self contained in this django app.
        class DummyRequest(object):
            META = {}
            def __init__(self):
                return
            def get_host(self):
                return 'edx.mit.edu'
            def is_secure(self):
                return False

        # Get course using the id, to pass to the grade function
        course = get_course_by_id(course_id)

        c_updated_students = 0
        for student in students:
            updated = False

            # Create dummy request and set its user and session
            request = DummyRequest()
            request.user = student
            request.session = {}

            # Call grade to get the gradeset
            gradeset = grades.grade(student, request, course, keep_raw_scores=False)

            # Get or create the overall grade for this student, save if needed
            course_grade, created = CourseGrade.objects.get_or_create(user=student, course_id=course_id)
            
            if created or not approx_equal(course_grade.percent, gradeset['percent']) or \
                    (course_grade.grade != gradeset['grade']):
                course_grade.percent = gradeset['percent']
                course_grade.grade = gradeset['grade']
                course_grade.save()
                updated = True

            student_problems = None

            # Iterate through the section_breakdown
            for section in gradeset['section_breakdown']:
                # If the dict has 'prominent' True this is at the assignment type level, store it if need
                if ('prominent' in section) and section['prominent']:
                    assign_type_grade, created = AssignmentTypeGrade.objects.get_or_create(user=student,
                                                                                           course_id=course_id,
                                                                                           category=section['category'])
                    if created or not approx_equal(assign_type_grade.percent, section['percent']):
                        assign_type_grade.percent = section['percent']
                        assign_type_grade.save()
                        updated = True

                else: #If no 'prominent' or it's False this is at the assignment level
                    store = True

                    # If the percent is 0, there are three possibilities:
                    # 1. There are no problems for that assignment yet -> skip section
                    # 2. The student hasn't submitted an answer to any of the problems for that assignment -> skip section
                    # 3. The student has submitted answers and got zero -> record
                    # Check for all three possibilities, only store for #3
                    if section['percent'] == 0:
                        # Find which assignment this is for this type/category
                        m = re.search('.* (\d+)', section['label'])
                        index = -1
                        if m:
                            index = int(m.group(1))-1
                        else:
                            print "WARNING: Can't find index for the following section, skipping"
                            print section
                            store = False # If there is no number, better to just not store it

                        # Check to see if the assignment hasn't been created yet or has no problems (#1 & #2)
                        if (index < 0) or (index >= len(assignment_problems_map[section['category']])) or \
                                (len(assignment_problems_map[section['category']][index]) == 0):
                            store = False
                        else:

                            # Get problems student has done, only do this database call if needed
                            if student_problems == None:
                                query = StudentModule.objects.filter(course_id__exact=course_id,
                                                                     grade__isnull=False,
                                                                     module_type__exact="problem",
                                                                     student=student
                                                                     ).values('module_state_key').distinct()

                                student_problems = []
                                for problem in query:
                                    student_problems.append(problem['module_state_key'])

                            if (not (set(assignment_problems_map[section['category']][index]) & set(student_problems))):
                                store = False

                    if store:
                        assign_grade, created = AssignmentGrade.objects.get_or_create(user=student,
                                                                                      course_id=course_id,
                                                                                      label=section['label'])
                        if created or not approx_equal(assign_grade.percent, section['percent']):
                            assign_grade.percent = section['percent']
                            assign_grade.save()
                            updated = True


            if updated:
                c_updated_students += 1

        c_all_students = len(students)
        print "--------------------------------------------------------------------------------"
        print "Done! Updated {0} students' grades out of {1}".format(c_updated_students, c_all_students)
        print "--------------------------------------------------------------------------------"

        # Save since everything finished successfully, log latest run.
        q_log = Log(script_id=script_id, course_id=course_id, created=tstart)
        q_log.save()
