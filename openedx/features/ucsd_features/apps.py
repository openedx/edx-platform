from django.apps import AppConfig


class UcsdFeatures(AppConfig):
    name = 'openedx.features.ucsd_features'

    def ready(self):
        super(UcsdFeatures, self).ready()
        from openedx.features.ucsd_features.signals import *
        from openedx.features.ucsd_features.additional_registration_fields import *
