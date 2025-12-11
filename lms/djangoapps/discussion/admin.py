"""
Django Admin configuration for discussion moderation models.

Following edX best practices:
- Read-only for most users (view-only audit logs)
- Write access restricted to superusers
- Staff can view but not modify
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from forum.backends.mysql.models import (
    DiscussionBan,
    DiscussionBanException,
    DiscussionModerationLog,
)


class ReadOnlyForNonSuperuserMixin:
    """
    Mixin to make admin read-only for non-superusers.

    Superusers can add/change/delete, but regular staff can only view.
    This is useful for audit/compliance access while preventing accidental changes.
    """

    def has_add_permission(self, request):
        """Only superusers can add new records."""
        if request.user.is_superuser:
            return super().has_add_permission(request)
        return False

    def has_change_permission(self, request, obj=None):
        """Only superusers can modify records. Staff can view."""
        if request.user.is_superuser:
            return super().has_change_permission(request, obj)
        # Staff users can view (needed for list view) but fields will be readonly
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete records."""
        if request.user.is_superuser:
            return super().has_delete_permission(request, obj)
        return False

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly for non-superusers."""
        if not request.user.is_superuser:
            # Return all fields as readonly for staff (non-superuser)
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)


@admin.register(DiscussionBan)
class DiscussionBanAdmin(ReadOnlyForNonSuperuserMixin, admin.ModelAdmin):
    """
    Admin interface for Discussion Bans.

    Permissions:
    - Superusers: Full access (view, add, change, delete)
    - Staff: View-only (for audit/support purposes)
    - Others: No access
    """

    list_display = [
        'id',
        'user_link',
        'scope',
        'course_or_org',
        'is_active',
        'banned_at',
        'banned_by_link',
        'reason_preview',
    ]

    list_filter = [
        'scope',
        'is_active',
        'banned_at',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'course_id',
        'org_key',
        'reason',
        'banned_by__username',
    ]

    readonly_fields = [
        'banned_at',
        'unbanned_at',
        'created',
        'modified',
    ]

    fieldsets = (
        (_('Ban Information'), {
            'fields': (
                'user',
                'scope',
                'course_id',
                'org_key',
                'is_active',
            )
        }),
        (_('Moderation Details'), {
            'fields': (
                'banned_by',
                'reason',
                'banned_at',
                'unbanned_by',
                'unbanned_at',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created',
                'modified',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'banned_at'

    def user_link(self, obj):
        """Display user with link to user admin."""
        if obj.user:
            from django.urls import reverse
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = _('User')

    def banned_by_link(self, obj):
        """Display moderator with link to user admin."""
        if obj.banned_by:
            from django.urls import reverse
            url = reverse('admin:auth_user_change', args=[obj.banned_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.banned_by.username)
        return '-'
    banned_by_link.short_description = _('Banned By')

    def course_or_org(self, obj):
        """Display either course_id or organization based on scope."""
        if obj.scope == 'course':
            return obj.course_id or '-'
        else:
            return obj.org_key or '-'
    course_or_org.short_description = _('Course/Org')

    def reason_preview(self, obj):
        """Display truncated reason."""
        if obj.reason:
            return obj.reason[:100] + '...' if len(obj.reason) > 100 else obj.reason
        return '-'
    reason_preview.short_description = _('Reason')


@admin.register(DiscussionBanException)
class DiscussionBanExceptionAdmin(ReadOnlyForNonSuperuserMixin, admin.ModelAdmin):
    """
    Admin interface for Ban Exceptions.

    Allows viewing course-specific exceptions to organization-level bans.
    """

    list_display = [
        'id',
        'ban_link',
        'course_id',
        'unbanned_by_link',
        'created',
    ]

    list_filter = [
        'created',
    ]

    search_fields = [
        'ban__user__username',
        'course_id',
        'unbanned_by__username',
        'reason',
    ]

    readonly_fields = [
        'created',
        'modified',
    ]

    fieldsets = (
        (_('Exception Information'), {
            'fields': (
                'ban',
                'course_id',
                'unbanned_by',
                'reason',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created',
                'modified',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'created'

    def ban_link(self, obj):
        """Display link to parent ban."""
        if obj.ban:
            from django.urls import reverse
            url = reverse('admin:discussion_discussionban_change', args=[obj.ban.id])
            return format_html(
                '<a href="{}">Ban #{} - {}</a>', url, obj.ban.id, obj.ban.user.username
            )
        return '-'
    ban_link.short_description = _('Parent Ban')

    def unbanned_by_link(self, obj):
        """Display unbanner with link."""
        if obj.unbanned_by:
            from django.urls import reverse
            url = reverse('admin:auth_user_change', args=[obj.unbanned_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.unbanned_by.username)
        return '-'
    unbanned_by_link.short_description = _('Unbanned By')


@admin.register(DiscussionModerationLog)
class DiscussionModerationLogAdmin(ReadOnlyForNonSuperuserMixin, admin.ModelAdmin):
    """
    Admin interface for Moderation Audit Logs.

    IMPORTANT: This is an audit log and should be READ-ONLY for all users
    (even superusers in production). Only use for compliance/investigation.
    """

    list_display = [
        'id',
        'action_type',
        'target_user_link',
        'moderator_link',
        'course_id',
        'scope',
        'created',
    ]

    list_filter = [
        'action_type',
        'scope',
        'created',
    ]

    search_fields = [
        'target_user__username',
        'target_user__email',
        'moderator__username',
        'course_id',
        'reason',
    ]

    readonly_fields = [
        'action_type',
        'target_user',
        'moderator',
        'course_id',
        'scope',
        'reason',
        'metadata',
        'created',
    ]

    fieldsets = (
        (_('Action Details'), {
            'fields': (
                'action_type',
                'target_user',
                'moderator',
                'course_id',
                'scope',
            )
        }),
        (_('Context'), {
            'fields': (
                'reason',
                'metadata',
            )
        }),
        (_('Timestamp'), {
            'fields': ('created',),
        }),
    )

    date_hierarchy = 'created'

    # Disable add/delete for audit logs - even for superusers
    def has_add_permission(self, request):
        """Audit logs should never be manually created."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs should never be deleted."""
        return False

    def target_user_link(self, obj):
        """Display target user with link."""
        if obj.target_user:
            from django.urls import reverse
            url = reverse('admin:auth_user_change', args=[obj.target_user.id])
            return format_html('<a href="{}">{}</a>', url, obj.target_user.username)
        return '-'
    target_user_link.short_description = _('Target User')

    def moderator_link(self, obj):
        """Display moderator with link."""
        if obj.moderator:
            from django.urls import reverse
            url = reverse('admin:auth_user_change', args=[obj.moderator.id])
            return format_html('<a href="{}">{}</a>', url, obj.moderator.username)
        return '-'
    moderator_link.short_description = _('Moderator')
