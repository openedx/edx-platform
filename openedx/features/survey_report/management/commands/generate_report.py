"""
CLI command to generate survey report.
"""

from django.core.management.base import BaseCommand, CommandError

from openedx.features.survey_report.api import generate_report, send_report_to_external_api


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

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-send',
            action='store_true',
            help='Do not send the report after generated.'
        )

    def handle(self, *_args, **options):
        try:
            report = generate_report()
            self.stdout.write(self.style.SUCCESS('Survey report has been generated successfully.'))
        except Exception as error:
            raise CommandError(f'An error has occurred while survey report was generating. {error}') from error

        if not options['no_send']:
            try:
                send_report_to_external_api(report_id=report)
                self.stdout.write(self.style.SUCCESS('Survey report has been sent successfully.'))
            except Exception as send_error:
                raise CommandError(
                    f'An error has occurred while survey report was sending. {send_error}'
                ) from send_error
