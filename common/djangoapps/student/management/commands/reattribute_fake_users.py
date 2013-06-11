# creates users named johndoen with emails of jdn@edx.org
# they are enrolled in 600x and have fake grades with

from optparse import make_option
import json
import random
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django.contrib.auth.models import User
from student.models import UserProfile, CourseEnrollment
from courseware.models import StudentModule


class Command(BaseCommand):

    args = '<>'
    help = """
    Add fake students and grades to db.
    """

    # option_list = BaseCommand.option_list + (
    #     make_option('--course_id',
    #                 action='store',
    #                 dest='course_id',
    #                 help='Specify a particular course.'),
    #     make_option('--exam_series_code',
    #                 action='store',
    #                 dest='exam_series_code',
    #                 default=None,
    #                 help='Specify a particular exam, using the Pearson code'),
    #     make_option('--accommodation_pending',
    #                 action='store_true',
    #                 dest='accommodation_pending',
    #                 default=False,
    #                 ),
    # )

    @transaction.autocommit
    def _process_user(self, user):
        def get_year_of_birth():
            if random.random() > 0.9:
                return None
            else:
                return random.triangular(UserProfile.this_year - 100, UserProfile.this_year, UserProfile.this_year - 22)

        user.profile.year_of_birth = get_year_of_birth()
        user.profile.save()

    def handle(self, *args, **options):
        map(self._process_user, User.objects.filter(username__contains="johndoe").select_related('profile'))
