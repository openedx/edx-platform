"""
A script to create some dummy users
"""
from __future__ import print_function
import uuid

from django.core.management.base import BaseCommand
from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from student.forms import AccountCreationForm
from student.helpers import do_create_account


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
    for __ in range(num):
        (user, _, _) = do_create_account(make_random_form())
        if course_key is not None:
            CourseEnrollment.enroll(user, course_key)
        print('Created user {}'.format(user.username))


class Command(BaseCommand):
    help = """Create N new users, with random parameters.

Usage: create_random_users.py N [course_id_to_enroll_in].

Examples:
  create_random_users.py 1
  create_random_users.py 10 MITx/6.002x/2012_Fall
  create_random_users.py 100 HarvardX/CS50x/2012
"""

    def add_arguments(self, parser):
        parser.add_argument('num_users',
                            help='Number of users to create',
                            type=int)
        parser.add_argument('course_key',
                            help='Add newly created users to this course',
                            nargs='?')

    def handle(self, *args, **options):
        num = options['num_users']
        course_key = CourseKey.from_string(options['course_key']) if options['course_key'] else None
        create(num, course_key)
