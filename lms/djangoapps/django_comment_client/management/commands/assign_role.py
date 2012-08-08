from django.core.management.base import BaseCommand, CommandError
from django_comment_client.models import Permission, Role
from django.contrib.auth.models import User


class Command(BaseCommand):
    args = 'user role course_id'
    help = 'Assign a role to a user'

    def handle(self, *args, **options):
        role = Role.objects.get(name=args[1], course_id=args[2])

        if '@' in args[0]:
            user = User.objects.get(email=args[0])
        else:
            user = User.objects.get(username=args[0])

        user.roles.add(role)