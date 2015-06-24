"""
Command to manually re-post open ended submissions to the grader.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from optparse import make_option

from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from xmodule.open_ended_grading_classes.open_ended_module import OpenEndedModule

from courseware.courses import get_course

from instructor.utils import get_module_for_student


class Command(BaseCommand):
    """
    Command to manually re-post open ended submissions to the grader.
    """

    help = ("Usage: openended_post <course_id> <problem_location> <student_ids.txt> <hostname> --dry-run --task-number=<task_number>\n"
            "The text file should contain a User.id in each line.")

    option_list = BaseCommand.option_list + (
        make_option('-n', '--dry-run',
                    action='store_true', dest='dry_run', default=False,
                    help="Do everything except send the submission to the grader. "),
        make_option('--task-number',
                    type='int', default=0,
                    help="Task number that needs to be submitted."),
    )

    def handle(self, *args, **options):

        dry_run = options['dry_run']
        task_number = options['task_number']

        if len(args) == 4:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(args[0])
            location = course_id.make_usage_key_from_deprecated_string(args[1])
            students_ids = [line.strip() for line in open(args[2])]
            hostname = args[3]
        else:
            print self.help
            return

        try:
            course = get_course(course_id)
        except ValueError as err:
            print err
            return

        descriptor = modulestore().get_item(location, depth=0)
        if descriptor is None:
            print "Location not found in course"
            return

        if dry_run:
            print "Doing a dry run."

        students = User.objects.filter(id__in=students_ids).order_by('username')
        print "Number of students: {0}".format(students.count())

        for student in students:
            post_submission_for_student(student, course, location, task_number, dry_run=dry_run, hostname=hostname)


def post_submission_for_student(student, course, location, task_number, dry_run=True, hostname=None):
    """If the student's task child_state is ASSESSING post submission to grader."""

    print "{0}:{1}".format(student.id, student.username)

    request = DummyRequest()
    request.user = student
    request.host = hostname

    try:
        module = get_module_for_student(student, location, request=request, course=course)
        if module is None:
            print "  WARNING: No state found."
            return False

        latest_task = module.child_module.get_task_number(task_number)
        if latest_task is None:
            print "  WARNING: No task state found."
            return False

        if not isinstance(latest_task, OpenEndedModule):
            print " ERROR: Not an OpenEndedModule task."
            return False

        latest_task_state = latest_task.child_state

        if latest_task_state == OpenEndedChild.INITIAL:
            print "  WARNING: No submission."
        elif latest_task_state == OpenEndedChild.POST_ASSESSMENT or latest_task_state == OpenEndedChild.DONE:
            print "  WARNING: Submission already graded."
        elif latest_task_state == OpenEndedChild.ASSESSING:
            latest_answer = latest_task.latest_answer()
            if dry_run:
                print "  Skipped sending submission to grader: {0!r}".format(latest_answer[:100].encode('utf-8'))
            else:
                latest_task.send_to_grader(latest_answer, latest_task.system)
                print "  Sent submission to grader: {0!r}".format(latest_answer[:100].encode('utf-8'))
                return True
        else:
            print "WARNING: Invalid task_state: {0}".format(latest_task_state)
    except Exception as err:  # pylint: disable=broad-except
        print err

    return False


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        self.host = None
        self.secure = True

    def get_host(self):
        """Return a default host."""
        return self.host

    def is_secure(self):
        """Always secure."""
        return self.secure
