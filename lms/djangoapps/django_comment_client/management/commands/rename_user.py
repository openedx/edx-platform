"""
Change the username of an existing user
"""
import logging
from os.path import basename

from pymongo.errors import PyMongoError

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from django.contrib.auth.models import User

from django_comment_client import management_utils

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    invoke this manage.py command from the console as follows:
    python manage.py lms rename_user <username1> <username2>
    """
    args = '<old_username> <new_username>'
    help = 'Modify the username of an existing user'

    def handle(self, *args, **options):
        """
        utilizes the rename_user function in the management_utils module
        :param args: <old_username> <new_username>
        :param options: no options supported
        """
        if len(args) != 2:
            command_name = '.'.join(basename(__file__).split('.')[:-1])
            raise CommandError(
                "Usage is {command_name} {command_args}".format(
                    command_name=command_name,
                    command_args=self.args,
                )
            )

        try:
            management_utils.rename_user(*args)
        except (User.DoesNotExist, IntegrityError, PyMongoError):
            log.exception('FAILED TO MODIFY USERNAME FOR USER: {old_username}'.format(
                old_username=args[0]
            ))
        else:
            print "Changed username of user: {old_username} to {new_username}".format(
                old_username=args[0],
                new_username=args[1],
            )
