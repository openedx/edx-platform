"""
Management command to seed default permissions and roles.
"""
from django.core.management.base import BaseCommand, CommandError
from django_comment_common.utils import seed_permissions_roles
from opaque_keys.edx.keys import CourseKey


class Command(BaseCommand):
    args = 'course_id'
    help = 'Seed default permisssions and roles'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("Please provide a course id")
        if len(args) > 1:
            raise CommandError("Too many arguments")
        course_id = CourseKey.from_string(args[0])

        seed_permissions_roles(course_id)
