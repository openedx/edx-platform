from django.core.management.base import BaseCommand
from lms.djangoapps.onboarding.helpers import get_current_utc_date, its_been_year
from oef.models import OrganizationOefUpdatePrompt

from logging import getLogger
log = getLogger(__name__)


class Command(BaseCommand):
    help = """
    Update Organization Oef Prompts.
    """

    def handle(self, *args, **options):
        current_date = get_current_utc_date()

        # Select those prompts whose finish_date is at least a year back from now
        prompts = OrganizationOefUpdatePrompt.objects.filter(
            latest_finish_date__lte=current_date.replace(year=current_date.year - 1)
        )
        for prompt in prompts:
            finish_date = prompt.latest_finish_date
            updated_year = its_been_year(finish_date)

            if updated_year != prompt.year:
                prompt.year = updated_year
                prompt.save()
            else:
                log.info('No change detected')
