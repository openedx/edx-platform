"""
Django Admin pages for Subscriptions.
"""

from django.contrib import admin

from openedx.features.subscriptions.models import UserSubscription


class UserSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for the "UserSubscription" object.
    """
    search_fields = ['user__email', 'user__username']
    list_display = ['username', 'subscription_type', 'expiration_date', 'max_allowed_courses', 'enrolled_course_ids', 'site']
    list_filter = ['subscription_type', 'site']
    filter_horizontal = ['course_enrollments', ]

    def username(self, obj):
        return obj.user.username

    def enrolled_course_ids(self, obj):
        return ', '.join([str(enrollment) for enrollment in obj.course_enrollments.values_list('course_id', flat=True)])


admin.site.register(UserSubscription, UserSubscriptionAdmin)
