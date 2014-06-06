##
## A script to create some dummy users

from django.core.management.base import BaseCommand
from student.models import CourseEnrollment

from student.views import _do_create_account, get_random_post_override


def create(n, course_id):
    """Create n users, enrolling them in course_id if it's not None"""
    for i in range(n):
        (user, user_profile, _) = _do_create_account(get_random_post_override())
        if course_id is not None:
            CourseEnrollment.enroll(user, course_id)


class Command(BaseCommand):
    help = """Create N new users, with random parameters.

Usage: create_random_users.py N [course_id_to_enroll_in].

Examples:
  create_random_users.py 1
  create_random_users.py 10 MITx/6.002x/2012_Fall
  create_random_users.py 100 HarvardX/CS50x/2012
"""

    def handle(self, *args, **options):
        if len(args) < 1 or len(args) > 2:
            print Command.help
            return

        n = int(args[0])
        course_id = args[1] if len(args) == 2 else None
        create(n, course_id)
