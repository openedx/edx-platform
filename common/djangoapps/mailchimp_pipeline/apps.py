from django.apps import AppConfig


class MailchimpPipelineConfig(AppConfig):
    name = u'mailchimp_pipeline'

    def ready(self):
        pass
