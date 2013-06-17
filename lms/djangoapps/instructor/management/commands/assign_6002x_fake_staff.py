# creates users named johndoen with emails of jdn@edx.org
# they are enrolled in 600x and have fake grades with

from optparse import make_option
import json
import random
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django.contrib.auth.models import User
from student.models import UserProfile, CourseEnrollment
from courseware.models import StudentModule
from courseware.courses import get_course_by_id

from instructor.access import allow_access, revoke_access


class Command(BaseCommand):

    args = '<>'
    help = """
    Add fake students and grades to db.
    """

    def _delete_all_jds(self):
        [student.delete() for student in User.objects.filter(username__contains="johndoe")]

    def handle(self, *args, **options):
        course_id = 'MITx/6.002x/2013_Spring'
        course = get_course_by_id(course_id)
        self.set_level(course, User.objects.get(email='jd101@edx.org'), 'instructor')
        self.set_level(course, User.objects.get(email='jd102@edx.org'), 'instructor')
        self.set_level(course, User.objects.get(email='jd103@edx.org'), 'instructor')
        self.set_level(course, User.objects.get(email='jd104@edx.org'), 'staff')
        self.set_level(course, User.objects.get(email='jd105@edx.org'), 'staff')
        self.set_level(course, User.objects.get(email='jd106@edx.org'), 'staff')
        self.set_level(course, User.objects.get(email='jd107@edx.org'), 'staff')
        self.set_level(course, User.objects.get(email='jd108@edx.org'), 'staff')
        self.set_level(course, User.objects.get(email='jd109@edx.org'), 'staff')

    def set_level(self, course, user, level):
        """ level is one of [None, 'staff', 'instructor'] """
        revoke_access(course, user, 'instructor')
        revoke_access(course, user, 'staff')

        if level == 'staff':
            allow_access(course, user, level)
        if level == 'instructor':
            allow_access(course, user, level)
