"""
Django Admin for Notifications
"""

from django.contrib import admin

from .models import Notification, CourseNotificationPreference


class NotificationAdmin(admin.ModelAdmin):
    pass


class CourseNotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Admin for Course Notification Preferences
    """
    model = CourseNotificationPreference
    list_display = ['get_username', 'course_id', 'notification_preference_config']

    @admin.display(description='Username', ordering='user__username')
    def get_username(self, obj):
        return obj.user.username


admin.site.register(Notification, NotificationAdmin)
admin.site.register(CourseNotificationPreference, CourseNotificationPreferenceAdmin)
