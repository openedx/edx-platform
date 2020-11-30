"""
Configurations for Mailchimp Pipeline
"""
from django.apps import AppConfig


class MailchimpPipelineConfig(AppConfig):
    """
    Application configuration for mailchimp pipeline.
    """
    name = u'openedx.adg.common.mailchimp_pipeline'

    def ready(self):
        """
        Connect signal handlers.
        """
        super(MailchimpPipelineConfig, self).ready()

        from . import handlers  # pylint: disable=unused-import
