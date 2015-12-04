"""
Command to get statistics about open ended problems.
"""
import csv
import time

from django.core.management.base import BaseCommand
from optparse import make_option

from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild

from courseware.courses import get_course
from courseware.models import StudentModule
from student.models import anonymous_id_for_user, CourseEnrollment

from instructor.utils import get_module_for_student


class Command(BaseCommand):
    """
    Command to get statistics about open ended problems.
    """

    help = "Usage: openended_stats <course_id> <problem_location> --task-number=<task_number>\n"

    option_list = BaseCommand.option_list + (
        make_option('--task-number',
                    type='int', default=0,
                    help="Task number to get statistics about."),
    )

    def handle(self, *args, **options):
        """Handler for command."""

        task_number = options['task_number']

        if len(args) == 2:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(args[0])
            usage_key = course_id.make_usage_key_from_deprecated_string(args[1])
        else:
            print self.help
            return

        try:
            course = get_course(course_id)
        except ValueError as err:
            print err
            return

        descriptor = modulestore().get_item(usage_key, depth=0)
        if descriptor is None:
            print "Location {0} not found in course".format(usage_key)
            return

        try:
            enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
            print "Total students enrolled in {0}: {1}".format(course_id, enrolled_students.count())

            calculate_task_statistics(enrolled_students, course, usage_key, task_number)

        except KeyboardInterrupt:
            print "\nOperation Cancelled"


def calculate_task_statistics(students, course, location, task_number, write_to_file=True):
    """Print stats of students."""

    stats = {
        OpenEndedChild.INITIAL: 0,
        OpenEndedChild.ASSESSING: 0,
        OpenEndedChild.POST_ASSESSMENT: 0,
        OpenEndedChild.DONE: 0
    }

    students_with_saved_answers = []
    students_with_ungraded_submissions = []  # pylint: disable=invalid-name
    students_with_graded_submissions = []  # pylint: disable=invalid-name
    students_with_no_state = []

    student_modules = StudentModule.objects.filter(module_state_key=location, student__in=students).order_by('student')
    print "Total student modules: {0}".format(student_modules.count())

    for index, student_module in enumerate(student_modules):
        if index % 100 == 0:
            print "--- {0} students processed ---".format(index)

        student = student_module.student
        print "{0}:{1}".format(student.id, student.username)

        module = get_module_for_student(student, location, course=course)
        if module is None:
            print "  WARNING: No state found"
            students_with_no_state.append(student)
            continue

        latest_task = module.child_module.get_task_number(task_number)
        if latest_task is None:
            print "  No task state found"
            students_with_no_state.append(student)
            continue

        task_state = latest_task.child_state
        stats[task_state] += 1
        print "  State: {0}".format(task_state)

        if task_state == OpenEndedChild.INITIAL:
            if latest_task.stored_answer is not None:
                students_with_saved_answers.append(student)
        elif task_state == OpenEndedChild.ASSESSING:
            students_with_ungraded_submissions.append(student)
        elif task_state == OpenEndedChild.POST_ASSESSMENT or task_state == OpenEndedChild.DONE:
            students_with_graded_submissions.append(student)

    print "----------------------------------"
    print "Time: {0}".format(time.strftime("%Y %b %d %H:%M:%S +0000", time.gmtime()))
    print "Course: {0}".format(course.id)
    print "Location: {0}".format(location)
    print "No state: {0}".format(len(students_with_no_state))
    print "Initial State: {0}".format(stats[OpenEndedChild.INITIAL] - len(students_with_saved_answers))
    print "Saved answers: {0}".format(len(students_with_saved_answers))
    print "Submitted answers: {0}".format(stats[OpenEndedChild.ASSESSING])
    print "Received grades: {0}".format(stats[OpenEndedChild.POST_ASSESSMENT] + stats[OpenEndedChild.DONE])
    print "----------------------------------"

    if write_to_file:
        filename = "stats.{0}.{1}".format(location.course, location.name)
        time_stamp = time.strftime("%Y%m%d-%H%M%S")
        with open('{0}.{1}.csv'.format(filename, time_stamp), 'wb') as csv_file:
            writer = csv.writer(csv_file, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
            for student in students_with_ungraded_submissions:
                writer.writerow(("ungraded", student.id, anonymous_id_for_user(student, None), student.username))
            for student in students_with_graded_submissions:
                writer.writerow(("graded", student.id, anonymous_id_for_user(student, None), student.username))
    return stats
