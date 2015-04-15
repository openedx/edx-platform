#!/usr/bin/python
"""
django management command: dump grades to csv files
for use by batch processes
"""
from instructor_task.api_helper import AlreadyRunningError, _reserve_task
from courseware.courses import get_course_by_id
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the task of student grade report of given course\n"
    help += "Usage: grade_report_csv course_id instructor_username \n"

    def handle(self, *args, **options):

        print "args = ", args

        if len(args) > 1:
            course_id = args[0]
            instructor_username = args[1]
        else:
            print self.help
            return
        course_key = None
        # parse out the course id into a coursekey
        try:
            course_key = CourseKey.from_string(course_id)
        # if it's not a new-style course key, parse it from an old-style
        # course key
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        try:
            _course = get_course_by_id(course_key)
        except Exception as err:
            print "-----------------------------------------------------------------------------"
            print "Sorry, cannot find course with id {}".format(course_id)
            print "Got exception {}".format(err)
            print "Please provide a valid course ID"
            return

        print "-----------------------------------------------------------------------------"
        print "Computing grades for {}".format(course_id)

        try:
          user = User.objects.filter(username=instructor_username)[0]
          _reserve_task(course_key, 'grade_course', '', {}, user)
        except AlreadyRunningError:
          print "Task is already running"