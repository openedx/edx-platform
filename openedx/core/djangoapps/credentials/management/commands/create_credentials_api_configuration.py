""" Command to create a credentials api configuration """
from django.core.management.base import BaseCommand, CommandError
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig


class Command(BaseCommand):
    """
    Creates a api configuration between LMS <--> Credentials service.
    This command is meant to be used in combination with other commands to
    create a fully connected path to awarding program certificates in devstack.
    """

    # pylint: disable=unused-argument
    def handle(self, *args, **kwargs):
        try:
            CredentialsApiConfig.objects.create(
                enabled=True,
                enable_learner_issuance=True,
            )
        except Exception as e:
            raise CommandError from e
