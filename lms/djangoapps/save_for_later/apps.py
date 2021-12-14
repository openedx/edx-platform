"""
save_for_later Application Configuration
"""


from django.apps import AppConfig


class SaveForLaterConfig(AppConfig):
    """
    Application Configuration for save_for_later.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms.djangoapps.save_for_later'
