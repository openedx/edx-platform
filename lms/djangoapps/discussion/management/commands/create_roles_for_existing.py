"""
This must be run only after seed_permissions_roles.py!

Creates default roles for all users currently in the database. Just runs through
Enrollments.
"""


from django.core.management.base import BaseCommand

from openedx.core.djangoapps.django_comment_common.models import assign_default_role_on_enrollment
from common.djangoapps.student.models import CourseEnrollment


class Command(BaseCommand):
    help = 'Seed default permisssions and roles.'

    def handle(self, *args, **options):
        print('Updated roles for ', end=' ')
        for i, enrollment in enumerate(CourseEnrollment.objects.filter(is_active=1), start=1):
            assign_default_role_on_enrollment(None, enrollment)
            if i % 1000 == 0:
                print('{0}...'.format(i), end=' ')
        print()
