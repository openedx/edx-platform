"""
Django Admin pages for Subscriptions.
"""

from django.contrib import admin

from openedx.features.subscriptions.models import UserSubscription, UserSubscriptionHistory


class UserSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for the "UserSubscription" object.
    """
    search_fields = ['user__email', 'user__username']
    list_display = ['username', 'subscription_type', 'expiration_date', 'max_allowed_courses', 'site']
    list_filter = ['subscription_type', 'site']
    readonly_fields = ['course_enrollments', ]
    ordering = ('-modified', '-created',)
    actions = None

    def username(self, obj):
        return obj.user.username

    def enrolled_course_ids(self, obj):
        return ', '.join([str(enrollment) for enrollment in obj.course_enrollments.values_list('course_id', flat=True)])

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserSubscriptionHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for the "UserSubscriptionHistory" object.
    """
    search_fields = ['user__email', 'user__username']
    list_display = [
        'username', 'subscription_type', 'expiration_date', 'max_allowed_courses', 'site', 'created', 'modified'
    ]
    list_filter = ['subscription_type', 'site']
    filter_horizontal = ['course_enrollments', ]
    actions = None

    def username(self, obj):
        return obj.user.username

    def enrolled_course_ids(self, obj):
        return ', '.join([str(enrollment) for enrollment in obj.course_enrollments.values_list('course_id', flat=True)])

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(UserSubscriptionHistory, UserSubscriptionHistoryAdmin)
