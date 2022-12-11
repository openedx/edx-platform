"""
CLI command to generate survey report.
"""

from django.core.management.base import BaseCommand, CommandError

from openedx.features.survey_report.api import generate_report, update_report
from openedx.features.survey_report.models import SURVEY_REPORT_GENERATED


class Command(BaseCommand):
    """
    Management command to generate a new survey report with
    non-sensitive data.
    """

    help = """
        This command will create a new survey report using some
        models to get:
        - Total number of courses offered
        - Currently active learners
        ...
        learners ever registered, and generated certificates.
        """

    def handle(self, *_args, **_options):
        try:
            survey_report_id = generate_report()
            data = {"state": SURVEY_REPORT_GENERATED}
            update_report(survey_report_id=survey_report_id, data=data)
        except Exception as error:
            raise CommandError(f'An error has occurred while survey report was generating. {error}') from error

        self.stdout.write(
            self.style.SUCCESS(f'Survey report has been generated successfully with ID #{survey_report_id}.')
        )
