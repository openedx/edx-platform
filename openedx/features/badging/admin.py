"""
Admin site bindings for badging models
"""
from django.contrib import admin

from .models import Badge, UserBadge


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    """
    Admin for badge model
    """
    list_display = ('name', 'type', 'threshold')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """
    Admin for the UserBadge model
    """
    list_display = ('user', 'badge', 'date_earned')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]
