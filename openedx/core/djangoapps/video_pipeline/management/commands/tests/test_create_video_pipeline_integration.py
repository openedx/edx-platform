"""
Tests for create_video_pipeline_integration management command.
"""


import ddt
from django.core.management import call_command
from django.test import TestCase
from openedx.core.djangoapps.video_pipeline.models import VideoPipelineIntegration


@ddt.ddt
class CreateVideoPipelineIntegration(TestCase):
    """
    Management command test class.
    """
    def setUp(self):
        super(CreateVideoPipelineIntegration, self).setUp()

    def assert_integration_created(self, args, options):
        """
        Verify that the integration record was created.
        """
        integration = VideoPipelineIntegration.current()

        for index, attr in enumerate(('client_name', 'api_url', 'service_username')):
            self.assertEqual(args[index], getattr(integration, attr))

        self.assertEqual(integration.enabled, options.get('enabled'))

    @ddt.data(
        (
            [
                'veda',
                'http://veda.edx.org/api/',
                'veda_service_user',
            ],
            {'enabled': False}
        ),
        (
            [
                'veda',
                'http://veda.edx.org/api/',
                'veda_service_user',
            ],
            {'enabled': True}
        ),
    )
    @ddt.unpack
    def test_integration_creation(self, args, options):
        """
        Verify that the create_video_pipeline_integration command works as expected.
        """
        call_command('create_video_pipeline_integration', *args, **options)
        self.assert_integration_created(args, options)

    def test_idempotency(self):
        """
        Verify that the command can be run repeatedly with the same args and options without any ill effects.
        """
        args = [
            'veda',
            'http://veda.edx.org/api/',
            'veda_service_user',
        ]
        options = {'enabled': False}

        call_command('create_video_pipeline_integration', *args, **options)
        self.assert_integration_created(args, options)

        # Verify that the command is idempotent
        call_command('create_video_pipeline_integration', *args, **options)
        self.assert_integration_created(args, options)

        # Verify that only one record exists
        self.assertEqual(VideoPipelineIntegration.objects.count(), 1)
