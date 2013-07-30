"""
Script for granting existing course instructors course creator privileges.

This script is only intended to be run once on a given environment.
"""
from auth.authz import get_users_with_instructor_role, get_users_with_staff_role
from course_creators.views import add_user_with_status_granted, add_user_with_status_unrequested
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

        for user in get_users_with_instructor_role():
            add_user_with_status_granted(admin, user)

        # Some users will be both staff and instructors. Those folks have been
        # added with status granted above, and add_user_with_status_unrequested
        # will not try to add them again if they already exist in the course creator database.
        for user in get_users_with_staff_role():
            add_user_with_status_unrequested(user)

        # There could be users who are not in either staff or instructor (they've
        # never actually done anything in Studio). I plan to add those as unrequested
        # when they first go to their dashboard.

        admin.delete()
