"""
Django admin pages for registration_extension app
"""
from django.contrib import admin

from .models import ExtendedUserProfile


@admin.register(ExtendedUserProfile)
class ExtendedUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company')
