"""
Management command `create_video_pipeline_integration` is used to create video pipeline integration record.
"""


from openedx.core.djangoapps.video_pipeline.models import VideoPipelineIntegration
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    # pylint: disable=missing-docstring

    help = 'Creates the video pipeline integration record.'

    def add_arguments(self, parser):
        parser.add_argument('client_name')
        parser.add_argument('api_url')
        parser.add_argument('service_username')
        parser.add_argument('--enabled', dest='enabled', action='store_true')

    def handle(self, **fields):
        VideoPipelineIntegration.objects.get_or_create(
            client_name=fields['client_name'],
            api_url=fields['api_url'],
            service_username=fields['service_username'],
            enabled=fields['enabled'],
        )
