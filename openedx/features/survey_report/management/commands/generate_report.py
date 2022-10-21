"""
CLI command to generate survey report.
"""

from django.core.management.base import BaseCommand, CommandError

from openedx.features.survey_report.application import generate_report


class Command(BaseCommand):
    """
    Management command to generate a new survey report with
    non-sensitive data.
    """

    help = """
        This command will create a new survey report using some
        models to get the total number oof courses offered, currently active learners,
        learners ever registered, and generated certificates.
        """

    def handle(self, *_args, **_options):
        try:
            generate_report()
        except Exception as error:
            raise CommandError('An error has occurred while report was generating.') from error

        self.stdout.write(self.style.SUCCESS('Survey report has been generated successfully.'))
