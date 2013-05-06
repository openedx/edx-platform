from django.core.management.base import BaseCommand, CommandError
from django_comment_common.utils import seed_permissions_roles


class Command(BaseCommand):
    args = 'course_id'
    help = 'Seed default permisssions and roles'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("Please provide a course id")
        if len(args) > 1:
            raise CommandError("Too many arguments")
        course_id = args[0]

        administrator_role = Role.objects.get_or_create(name="Administrator", course_id=course_id)[0]
        moderator_role = Role.objects.get_or_create(name="Moderator", course_id=course_id)[0]
        community_ta_role = Role.objects.get_or_create(name="Community TA", course_id=course_id)[0]
        student_role = Role.objects.get_or_create(name="Student", course_id=course_id)[0]

        seed_permissions_roles(course_id)
