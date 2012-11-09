import uuid
from datetime import datetime
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from student.models import TestCenterUser

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--client_candidate_id',
            action='store',
            dest='client_candidate_id',
            help='ID we assign a user to identify them to Pearson'
        ),        
        make_option(
            '--first_name',
            action='store',
            dest='first_name',
        ),        
        make_option(
            '--last_name',
            action='store',
            dest='last_name',
        ),        
        make_option(
            '--address_1',
            action='store',
            dest='address_1',
        ),        
        make_option(
            '--city',
            action='store',
            dest='city',
        ),        
        make_option(
            '--state',
            action='store',
            dest='state',
            help='Two letter code (e.g. MA)'
        ),        
        make_option(
            '--postal_code',
            action='store',
            dest='postal_code',
        ),
        make_option(
            '--country',
            action='store',
            dest='country',
            help='Three letter country code (ISO 3166-1 alpha-3), like USA'
        ),
        make_option(
            '--phone',
            action='store',
            dest='phone',
            help='Pretty free-form (parens, spaces, dashes), but no country code'
        ),        
        make_option(
            '--phone_country_code',
            action='store',
            dest='phone_country_code',
            help='Phone country code, just "1" for the USA'
        ),
    )
    args = "<student_username>"
    help = "Create a TestCenterUser entry for a given Student"

    @staticmethod
    def is_valid_option(option_name):
        base_options = set(option.dest for option in BaseCommand.option_list)
        return option_name not in base_options


    def handle(self, *args, **options):
        username = args[0]
        print username

        our_options = dict((k, v) for k, v in options.items()
                           if Command.is_valid_option(k))
        student = User.objects.get(username=username)
        student.test_center_user = TestCenterUser(**our_options)
        student.test_center_user.save()
