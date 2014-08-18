"""
OAuth2 provider Django admin interface
"""
from django.contrib import admin

from oauth2_provider.models import TrustedClient


class TrustedClientAdmin(admin.ModelAdmin):
    "Django admin configuration for `TrustedClient` model"
    list_display = ('client',)


admin.site.register(TrustedClient, TrustedClientAdmin)
