"""
Script for granting existing course instructors course creator privileges.

This script is only intended to be run once on a given environment.
"""
from auth.authz import _grant_instructors_creator_access
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from django.db.utils import IntegrityError


class Command(BaseCommand):
    """
    Script for granting existing course instructors course creator privileges.
    """
    help = 'Grants all users with INSTRUCTOR role permission to create courses'

    def handle(self, *args, **options):
        """
        The logic of the command.
        """
        username = 'populate_creators_command'
        email = 'grant+creator+access@edx.org'
        try:
            admin = User.objects.create_user(username, email, 'foo')
            admin.is_staff = True
            admin.save()
        except IntegrityError:
            # If the script did not complete the last time it was run,
            # the admin user will already exist.
            admin = User.objects.get(username=username, email=email)

        _grant_instructors_creator_access(admin)
        admin.delete()
