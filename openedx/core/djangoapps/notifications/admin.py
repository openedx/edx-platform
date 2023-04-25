"""
Django Admin for Notifications
"""

from django.contrib import admin

from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    pass

admin.site.register(Notification, NotificationAdmin)
