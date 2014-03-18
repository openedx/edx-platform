"""
This must be run only after seed_permissions_roles.py!

Creates default roles for all users in the provided course. Just runs through
Enrollments.
"""
from django.core.management.base import BaseCommand, CommandError

from student.models import CourseEnrollment
from django_comment_common.models import assign_default_role_on_enrollment


class Command(BaseCommand):
    args = 'course_id'
    help = 'Add roles for all users in a course'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("Please provide a course id")
        if len(args) > 1:
            raise CommandError("Too many arguments")
        course_id = args[0]

        print "Updated roles for ",
        for i, enrollment in enumerate(CourseEnrollment.objects.filter(course_id=course_id, is_active=1), start=1):
            assign_default_role_on_enrollment(None, enrollment)
            if i % 1000 == 0:
                print "{0}...".format(i),
        print
