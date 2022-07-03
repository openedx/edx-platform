from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from openedx.features.funix_relative_date.models import (
	FunixRelativeDate
)

admin.site.register(FunixRelativeDate)
