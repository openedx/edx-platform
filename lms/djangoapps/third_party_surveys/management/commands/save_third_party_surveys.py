import logging

from django.core.management import BaseCommand

from third_party_surveys.tasks import get_third_party_surveys

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to get latest surveys from Survey Gizmo and store in DB.

    Examples:

        ./manage.py save_third_party_surveys
    """

    help = "Get Survey Gizmo Surveys"

    def handle(self, *args, **options):
        logger.info("Started task get_third_party_surveys")
        get_third_party_surveys()
        logger.info("Successfully finished task get_third_party_surveys")
