"""
This module contains classes controlling Django admin integration.
"""
from django.contrib import admin
from .models import EntitlementModel, EntitlementGroup


@admin.register(EntitlementModel)
class EntitlementAdmin(admin.ModelAdmin):
    pass


@admin.register(EntitlementGroup)
class EntitlementGroupAdmin(admin.ModelAdmin):
    pass

