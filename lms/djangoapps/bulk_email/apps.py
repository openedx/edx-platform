from django.apps import AppConfig


class BulkEmailConfig(AppConfig):
    """
    Application Configuration for bulk_email.
    """
    name = u'lms.djangoapps.bulk_email'

    def ready(self):
        """
        Ensure tasks are registered and signals connected.
        """
        from . import signals, tasks  # pylint: disable=unused-import
