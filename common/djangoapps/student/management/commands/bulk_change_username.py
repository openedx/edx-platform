"""
WARNING: This command is only meant to be used as part of a larger job that
updates usernames across all services. DO NOT run this alone or users will
not match across the system and things will be broken.

Command to take a list of usernames with preferred new username and update all
instances of that username in the edxapp database.
"""

import csv
import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# (model_name, column_name)
MODELS_WITH_USERNAME = (
    ('auth.user', 'username'),
    ('consent.DataSharingConsent', 'username'),
    ('consent.HistoricalDataSharingConsent', 'username'),
    ('credit.CreditEligibility', 'username'),
    ('credit.CreditRequest', 'username'),
    ('credit.CreditRequirementStatus', 'username'),
    ('user_api.UserRetirementPartnerReportingStatus', 'original_username'),
    ('user_api.UserRetirementStatus', 'original_username')
)


class Command(BaseCommand):
    """
    CSV should be in the format:
        currentusername1,desiredusername1
        currentusername2,desiredusername2

    Example usage:
        $ ./manage.py lms bulk_change_username learner_courses_to_recalculate.csv
    """
    help = "Updates all users' usernames in all edxapp tables that store username"

    def add_arguments(self, parser):
        parser.add_argument('csv')

    def handle(self, *args, **options):
        filename = options['csv']
        suffix_length = getattr(settings, 'SOCIAL_AUTH_UUID_LENGTH', 4)
        overwrite_locations = self.load_models()

        with open(filename) as csv_file:
            csv_reader = csv.DictReader(csv_file, fieldnames=['current_username', 'desired_username'])
            for row in csv_reader:
                new_username = row['desired_username']

                # Generate unique usernames from the desired_username until one doesn't already exist
                while True:
                    if User.objects.filter(username=new_username).exists():
                        unique_suffix = uuid.uuid4().hex[:suffix_length]
                        # In the rare chance that the generated username already exists, only swap the unique suffix
                        if new_username == row['desired_username']:
                            new_username = new_username + unique_suffix
                        else:
                            new_username = new_username[:-suffix_length] + unique_suffix
                    else:
                        break
                self.update_username_for_models(overwrite_locations, row['current_username'], new_username)

    def load_models(self):
        try:
            overwrite_locations = [(apps.get_model(model), column) for (model, column) in MODELS_WITH_USERNAME]
        except LookupError:
            raise CommandError("Unable to import all necessary models. Exiting command")
        return overwrite_locations

    def update_username_for_models(self, overwrite_locations, current_username, new_username):
        """
        Updates usernames in all necessary tables.
        Params:
            overwrite_locations: list of (<imported model>, <column to be change>) for all columns that required changing.
            current_username: user's current username
            new_username: new username that is already checked for duplicates

        Returns: Tuple of declaring if the change was successful and the message to log
            (is_successful, message)
        """
        try:
            with transaction.atomic():
                for (model, column) in overwrite_locations:
                    model.objects.filter(**{column: current_username}).update(**{column: new_username})
        except Exception as e:
            self.stderr.write("Unable to change username from {current} to {new}. Reason: {error}".format(
                current=current_username,
                new=new_username,
                error=e,
            ))
            return

        self.stdout.write("Successfully changed username from {current} to {new}".format(
            current=current_username,
            new=new_username,
        ))
