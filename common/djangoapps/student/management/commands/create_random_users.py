"""
A script to create some dummy users
"""
import uuid

from django.core.management.base import BaseCommand
from student.models import CourseEnrollment
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.forms import AccountCreationForm
from student.views import _do_create_account


def make_random_form():
    """
    Generate unique user data for dummy users.
    """
    identification = uuid.uuid4().hex[:8]
    return AccountCreationForm(
        data={
            'username': 'user_{id}'.format(id=identification),
            'email': 'email_{id}@example.com'.format(id=identification),
            'password': '12345',
            'name': 'User {id}'.format(id=identification),
        },
        tos_required=False
    )


def create(num, course_key):
    """Create num users, enrolling them in course_key if it's not None"""
    for idx in range(num):
        (user, _, _) = _do_create_account(make_random_form())
        if course_key is not None:
            CourseEnrollment.enroll(user, course_key)


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

        num = int(args[0])

        if len(args) == 2:
            try:
                course_key = CourseKey.from_string(args[1])
            except InvalidKeyError:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(args[1])
        else:
            course_key = None

        create(num, course_key)
