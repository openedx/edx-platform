"""
Defines the app name and connects the signal handlers associated with the mailchimp_pipeline app
"""
from django.apps import AppConfig


class MailchimpPipelineConfig(AppConfig):
    name = u'mailchimp_pipeline'

    def ready(self):
        pass
