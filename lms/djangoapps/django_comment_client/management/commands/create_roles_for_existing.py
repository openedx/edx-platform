"""
This must be run only after seed_permissions_roles.py!

Creates default roles for all users currently in the database. Just runs through
Enrollments.
"""
from django.core.management.base import BaseCommand, CommandError

from student.models import CourseEnrollment
from django_comment_common.models import assign_default_role_on_enrollment


class Command(BaseCommand):
    args = 'course_id'
    help = 'Seed default permisssions and roles'

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("This Command takes no arguments")

        print "Updated roles for ",
        for i, enrollment in enumerate(CourseEnrollment.objects.filter(is_active=1), start=1):
            assign_default_role_on_enrollment(None, enrollment)
            if i % 1000 == 0:
                print "{0}...".format(i),
        print
