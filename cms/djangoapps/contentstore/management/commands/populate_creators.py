from auth.authz import _grant_instructors_creator_access
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Grants all users with INSTRUCTOR role permission to create courses'

    def handle(self, *args, **options):
        admin = User.objects.create_user('populate_creators_command', 'grant+creator+access@edx.org', 'foo')
        admin.is_staff = True
        _grant_instructors_creator_access(admin)
        admin.delete()
