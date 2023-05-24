"""
Django Admin for Notifications
"""

from django.contrib import admin

from .models import Notification, NotificationPreference


class NotificationAdmin(admin.ModelAdmin):
    pass


class NotificationPreferenceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationPreference, NotificationPreferenceAdmin)
