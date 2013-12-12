#!/usr/bin/python
#
# Admin command for open ended problems.

from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from ...utils import get_descriptor, get_module_for_student, get_enrolled_students
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Admin command for open ended problems."""

    help = "Usage: openended_stats course_id location \n"

    def handle(self, *args, **options):
        """Handler for command."""

        print "args = ", args

        if len(args) > 0:
            course_id = args[0]
            location = args[1]
        else:
            print self.help
            return

        descriptor = get_descriptor(course_id, location)
        if descriptor is None:
            print "Location not found in course"
            return

        enrolled_students = get_enrolled_students(course_id)
        print "Total students enrolled: {0}".format(enrolled_students.count())

        self.get_state_counts(enrolled_students, course_id, location)

    def get_state_counts(self, students, course_id, location):
        """Print stats of students."""

        stats = {
            OpenEndedChild.INITIAL: 0,
            OpenEndedChild.ASSESSING: 0,
            OpenEndedChild.POST_ASSESSMENT: 0,
            OpenEndedChild.DONE: 0
        }

        for index, student in enumerate(students):
            if index % 100 == 0:
                print "{0} students processed".format(index)

            module = get_module_for_student(student, course_id, location)
            latest_task = module._xmodule.child_module.get_latest_task()
            stats[latest_task.child_state] += 1

        print stats
