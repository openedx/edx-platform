"""
Admin configuration for custom settings app models
"""
from django.contrib import admin

from .models import CustomSettings

admin.site.register(CustomSettings)
