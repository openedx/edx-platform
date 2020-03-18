from django.apps import AppConfig


class UcsdFeatures(AppConfig):
    name = 'openedx.features.ucsd_features'

    def ready(self):
        super(UcsdFeatures, self).ready()
        from .signals import *
        from .additional_registration_fields import *
