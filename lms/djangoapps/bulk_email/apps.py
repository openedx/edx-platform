# lint-amnesty, pylint: disable=missing-module-docstring
from django.apps import AppConfig


class BulkEmailConfig(AppConfig):
    """
    Application Configuration for bulk_email.
    """
    name = 'lms.djangoapps.bulk_email'
<<<<<<< HEAD
=======

    def ready(self):
        import lms.djangoapps.bulk_email.signals  # lint-amnesty, pylint: disable=unused-import
        from edx_ace.signals import ACE_MESSAGE_SENT  # lint-amnesty, pylint: disable=unused-import
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
