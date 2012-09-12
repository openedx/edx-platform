from django.core.management.base import BaseCommand, CommandError
from django_comment_client.models import Permission, Role


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
        student_role = Role.objects.get_or_create(name="Student", course_id=course_id)[0]

        for per in ["vote", "update_thread", "follow_thread", "unfollow_thread",
                       "update_comment", "create_sub_comment", "unvote" , "create_thread",
                       "follow_commentable", "unfollow_commentable", "create_comment", ]:
            student_role.add_permission(per)

        for per in ["edit_content", "delete_thread", "openclose_thread",
                        "endorse_comment", "delete_comment"]:
            moderator_role.add_permission(per)

        for per in ["manage_moderator"]:
            administrator_role.add_permission(per)

        moderator_role.inherit_permissions(student_role)

        administrator_role.inherit_permissions(moderator_role)
