from django.db import models

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel

class TestStackedOverrides(StackedConfigurationModel):
    STACKABLE_FIELDS = ['enabled', 'value']

    value = models.TextField(default=None)
