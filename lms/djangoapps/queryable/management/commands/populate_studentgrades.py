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

from queryable.models import Log, CourseGrade, AssignmentTypeGrade, AssignmentGrade
from queryable import util


################## Helper Functions ##################
def update_course_grade(course_grade, gradeset):
    """
    Returns true if the course grade needs to be updated.
    """
    return (not util.approx_equal(course_grade.percent, gradeset['percent'])) or (course_grade.grade != gradeset['grade'])


def get_assignment_index(assignment):
    """
    Returns the assignment's index, -1 if an index can't be found.

    `assignment` is a string formatted like this "HW 02" and this function returns 2 in this case.

    The string is the 'label' for each section in the 'section_breakdown' of the dictionary returned by the grades.grade
    function.
    """

    m = re.search('.* (\d+)', assignment)
    index = -1
    if m:
        index = int(m.group(1))-1

    return index


def assignment_exists_and_has_problems(assignment_problems_map, category, index):
    """
    Returns True if the assignment for the category and index exists and has problems

    `assignment_problems_map` a dictionary returned by get_assignment_to_problem_map(course_id)

    `category` string specifying the category or assignment type for this assignment

    `index` zero-based indexing into the array of assignments for that category
    """

    if index < 0:
        return False

    if category not in assignment_problems_map:
        return False

    if index >= len(assignment_problems_map[category]):
        return False

    return len(assignment_problems_map[category][index]) > 0


def get_student_problems(course_id, student):
    """
    Returns an array of problem ids that the student has answered for this course.

    `course_id` the course ID for the course interested in

    `student` the student want to get his/her problems

    Queries the database to get the problems the student has submitted an answer to for the course specified.
    """

    query = StudentModule.objects.filter(
        course_id__exact=course_id,
        student=student,
        grade__isnull=False,
        module_type__exact='problem',
    ).values('module_state_key').distinct()
    
    student_problems = []
    for problem in query:
        student_problems.append(problem['module_state_key'])

    return student_problems


def student_did_problems(student_problems, problem_set):
    """
    Returns true if `student_problems` and `problem_set` share problems.

    `student_problems` array of problem ids the student has done

    `problem_set` array of problem ids
    """

    return (set(student_problems) & set(problem_set))


def store_course_grade_if_need(student, course_id, gradeset):
    """
    Stores the course grade for the student and course if needed, returns True if it was stored

    `student` is a User object representing the student

    `course_id` the course's ID

    `gradeset` the values returned by grades.grade

    The course grade is stored if it has never been stored before (i.e. this is a new row in the database) or
    update_course_grade is true.
    """

    course_grade, created = CourseGrade.objects.get_or_create(user=student, course_id=course_id)

    if created or update_course_grade(course_grade, gradeset):
        course_grade.percent = gradeset['percent']
        course_grade.grade = gradeset['grade']
        course_grade.save()
        return True

    return False


def store_assignment_type_grade_if_need(student, course_id, category, percent):
    """
    Stores the assignment type grade for the student and course if needed, returns True if it was stored

    `student` is a User object representing the student

    `course_id` the course's ID

    `category` the category for the assignment type, found in the return value of the grades.grade function

    `percent` the percent grade the student received for this assignment

    The assignment type grade is stored if it has never been stored before (i.e. this is a new row in the database) or
    if the percent value is different than what is currently in the database.
    """

    assign_type_grade, created = AssignmentTypeGrade.objects.get_or_create(
        user=student,
        course_id=course_id,
        category=category,
    )

    if created or not util.approx_equal(assign_type_grade.percent, percent):
        assign_type_grade.percent = percent
        assign_type_grade.save()
        return True

    return False


def store_assignment_grade_if_need(student, course_id, label, percent):
    """
    Stores the assignment grade for the student and course if needed, returns True if it was stored

    `student` is a User object representing the student

    `course_id` the course's ID

    `label` the label for the assignment, found in the return value of the grades.grade function

    `percent` the percent grade the student received for this assignment

    The assignment grade is stored if it has never been stored before (i.e. this is a new row in the database) or
    if the percent value is different than what is currently in the database.
    """

    assign_grade, created = AssignmentGrade.objects.get_or_create(
        user=student,
        course_id=course_id,
        label=label,
    )

    if created or not util.approx_equal(assign_grade.percent, percent):
        assign_grade.percent = percent
        assign_grade.save()
        return True

    return False

################## Actual Command ##################
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

        assignment_problems_map = util.get_assignment_to_problem_map(course_id)

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
            student_problems = None

            # Create dummy request and set its user and session
            request = DummyRequest()
            request.user = student
            request.session = {}

            # Call grade to get the gradeset
            gradeset = grades.grade(student, request, course, keep_raw_scores=False)

            updated = store_course_grade_if_need(student, course_id, gradeset)

            # Iterate through the section_breakdown
            for section in gradeset['section_breakdown']:
                # If the dict has 'prominent' and it's True this is at the assignment type level, store it if need
                if ('prominent' in section) and section['prominent']:
                    updated = store_assignment_type_grade_if_need(
                        student, course_id, section['category'], section['percent']
                    )

                else: #If no 'prominent' or it's False this is at the assignment level
                    store = False

                    # If the percent is 0, there are three possibilities:
                    # 1. There are no problems for that assignment yet -> skip section
                    # 2. The student hasn't submitted an answer to any problem for that assignment -> skip section
                    # 3. The student has submitted answers and got zero -> record
                    # Only store for #3
                    if section['percent'] > 0:
                        store = True
                    else:
                        # Find which assignment this is for this type/category
                        index = get_assignment_index(section['label'])
                        if index < 0:
                            print "WARNING: Can't find index for the following section, skipping"
                            print section
                        else:
                            if assignment_exists_and_has_problems(assignment_problems_map, section['category'], index):

                                # Get problems student has done, only do this database call if needed
                                if student_problems == None:
                                    student_problems = get_student_problems(course_id, student)
                                    
                                curr_assignment_problems = assignment_problems_map[section['category']][index]
                                    
                                if student_did_problems(student_problems, curr_assignment_problems):
                                    store = True

                    if store:
                        updated = store_assignment_grade_if_need(
                            student, course_id, section['label'], section['percent']
                        )

            if updated:
                c_updated_students += 1

        c_all_students = len(students)
        print "--------------------------------------------------------------------------------"
        print "Done! Updated {0} students' grades out of {1}".format(c_updated_students, c_all_students)
        print "--------------------------------------------------------------------------------"

        # Save since everything finished successfully, log latest run.
        q_log = Log(script_id=script_id, course_id=course_id, created=tstart)
        q_log.save()
