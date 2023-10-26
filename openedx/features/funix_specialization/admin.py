from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from openedx.features.funix_specialization.models import (
	FunixSpecialization
)

admin.site.register(FunixSpecialization)
