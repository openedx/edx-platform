"""
A command to update organization metric prompts and sync updates with mailchimp
"""
from logging import getLogger

from django.core.management.base import BaseCommand

from lms.djangoapps.onboarding.helpers import (
    get_current_utc_date,
    its_been_year,
    its_been_year_month,
    its_been_year_six_month,
    its_been_year_three_month
)
from lms.djangoapps.onboarding.models import OrganizationMetricUpdatePrompt

log = getLogger(__name__)


def is_prompt_values_are_same(prompt, year, year_month, year_three_month, year_six_month):
    """
    :param prompt: prompt object
    :param year: bool, updated year
    :param year_month: bool, updated year_month
    :param year_three_month: bool, updated_year_three_month
    :param year_six_month: bool, updated_year_six_month
    :return: True if any attribute of old and updated prompt and are not matching
    """
    return all((
        prompt.year == year,
        prompt.year_month == year_month,
        prompt.year_three_month == year_three_month,
        prompt.year_six_month == year_six_month
    ))


class Command(BaseCommand):
    """
    A command to update organization metric prompts and sync updates with mailchimp
    """

    help = """
    Update Organization Metric Prompts.
    And sync the updates with mailchimp
    """

    def handle(self, *args, **options):
        current_date = get_current_utc_date()

        # Select those prompts whose lates_metric submission is at least a year back from now
        prompts = OrganizationMetricUpdatePrompt.objects.filter(
            latest_metric_submission__lte=current_date.replace(year=current_date.year - 1)
        )
        for prompt in prompts:
            submission_date = prompt.latest_metric_submission
            updated_year = its_been_year(submission_date)
            updated_year_month = its_been_year_month(submission_date)
            updated_year_three_month = its_been_year_three_month(submission_date)
            updated_year_six_month = its_been_year_six_month(submission_date)
            is_prompt_same = is_prompt_values_are_same(
                prompt,
                year=updated_year,
                year_month=updated_year_month,
                year_three_month=updated_year_three_month,
                year_six_month=updated_year_six_month
            )

            if not is_prompt_same:
                prompt.year = updated_year
                prompt.year_month = updated_year_month
                prompt.year_three_month = updated_year_three_month
                prompt.year_six_month = updated_year_six_month
                # if remind_me_later is True it's means that now we have to set it to None
                # Because it's next trigger now
                if prompt.remind_me_later:
                    prompt.remind_me_later = None
                prompt.save()
            else:
                log.info('No change detected')
