"""
Django Admin for Notifications
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .base_notification import COURSE_NOTIFICATION_APPS, COURSE_NOTIFICATION_TYPES
from .models import CourseNotificationPreference, Notification


class NotificationAppNameListFilter(admin.SimpleListFilter):
    """
    Shows list filter in django admin of notification apps
    """
    title = _("Notification App")
    parameter_name = "app_name"

    def lookups(self, request, model_admin):
        lookup_list = [
            (app_name, app_name)
            for app_name in COURSE_NOTIFICATION_APPS.keys()
        ]
        return lookup_list

    def queryset(self, request, queryset):
        app_name = self.value()
        if app_name not in COURSE_NOTIFICATION_APPS.keys():
            return queryset
        return queryset.filter(app_name=app_name)


class NotificationTypeListFilter(admin.SimpleListFilter):
    """
    Shows list filter in django admin of notification types
    """
    title = _("Notification Type")
    parameter_name = "notification_type"

    def lookups(self, request, model_admin):
        lookup_list = [
            (notification_type, notification_type)
            for notification_type in COURSE_NOTIFICATION_TYPES.keys()
        ]
        return lookup_list

    def queryset(self, request, queryset):
        notification_type = self.value()
        if notification_type not in COURSE_NOTIFICATION_TYPES.keys():
            return queryset
        return queryset.filter(notification_type=notification_type)


class NotificationAdmin(admin.ModelAdmin):
    """
    Admin for Notifications
    """
    raw_id_fields = ('user',)
    search_fields = ('course_id', 'app_name', 'notification_type', 'user__username')
    list_filter = (NotificationAppNameListFilter, NotificationTypeListFilter)


class CourseNotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Admin for Course Notification Preferences
    """
    model = CourseNotificationPreference
    raw_id_fields = ('user',)
    list_display = ('get_username', 'course_id', 'notification_preference_config')
    search_fields = ('course_id', 'user__username')

    @admin.display(description='Username', ordering='user__username')
    def get_username(self, obj):
        return obj.user.username


admin.site.register(Notification, NotificationAdmin)
admin.site.register(CourseNotificationPreference, CourseNotificationPreferenceAdmin)
