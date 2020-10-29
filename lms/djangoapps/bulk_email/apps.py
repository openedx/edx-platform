from django.apps import AppConfig


class BulkEmailConfig(AppConfig):
    """
    Application Configuration for bulk_email.
    """
    name = u'lms.djangoapps.bulk_email'


class BulkEmailCeleryConfig(AppConfig):
    """
    Celery-specific App config to force the loading of tasks.

    This will break tests if loaded as the normal AppConfig in INSTALLED_APPS
    outside of celery.
    """
    def ready(self):
        # noinspection PyUnresolvedReferences
        super().ready()
        from . import tasks  # pylint: disable=unused-import
