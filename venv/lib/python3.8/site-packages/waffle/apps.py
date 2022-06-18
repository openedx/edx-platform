from django.apps import AppConfig


class WaffleConfig(AppConfig):
    name = 'waffle'
    verbose_name = 'django-waffle'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        import waffle.signals  # noqa: F401
