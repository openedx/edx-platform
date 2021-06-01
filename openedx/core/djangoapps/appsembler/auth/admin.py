"""Provie access to Appsembler Auth models in the admin dashboard
"""
from django.contrib import admin

from .models import TrustedApplication


@admin.register(TrustedApplication)
class TrustedApplicationAdmin(admin.ModelAdmin):
    """
    TODO: Add filtering on application properties
    TODO: Consider adding search
    """
    list_display = ('id', 'application')
