#!/usr/bin/python
#
# django management command: dump grades to csv files
# for use by batch processes

from ...utils import get_descriptor, read_csv, get_affected_students_from_ids, get_module_for_student
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Usage: posts problem to xqueue \n"

    def handle(self, *args, **options):

        print "args = ", args

        if len(args) > 0:
            course_id = args[0]
            location = args[1]
            affected_students_ids = read_csv(args[2])
        else:
            print self.help
            return

        descriptor = get_descriptor(course_id, location)
        if descriptor is None:
            print "Location not found in course"
            return

        affected_students = get_affected_students_from_ids(affected_students_ids)

        for student in affected_students:
            try:
                module = get_module_for_student(student, course_id, location)
                latest_task = module._xmodule.child_module.get_latest_task()
                latest_task.send_to_grader(latest_task.latest_answer(), latest_task.system)
            except Exception as err:
                print err
