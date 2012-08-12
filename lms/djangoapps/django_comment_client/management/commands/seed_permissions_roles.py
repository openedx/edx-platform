from django.core.management.base import BaseCommand, CommandError
from django_comment_client.models import Permission, Role


class Command(BaseCommand):
    args = ''
    help = 'Seed default permisssions and roles'

    def handle(self, *args, **options):
        moderator_role = Role.objects.get_or_create(name="Moderator", course_id="MITx/6.002x/2012_Fall")[0]
        student_role = Role.objects.get_or_create(name="Student", course_id="MITx/6.002x/2012_Fall")[0]

        for per in ["vote", "update_thread", "follow_thread", "unfollow_thread",
                       "update_comment", "create_sub_comment", "unvote" , "create_thread",
                       "follow_commentable", "unfollow_commentable", "create_comment", ]:
            student_role.add_permission(per)

        for per in ["edit_content", "delete_thread", "openclose_thread",
                        "endorse_comment", "delete_comment"]:
            moderator_role.add_permission(per)

        moderator_role.inherit_permissions(student_role)
