"""
Django admin configuration pages for the user_api app
"""
from django.contrib import admin

from .models import UserRetirementPartnerReportingStatus, RetirementState, UserRetirementStatus, UserRetirementRequest


@admin.register(RetirementState)
class RetirementStateAdmin(admin.ModelAdmin):
    """
    Admin interface for the RetirementState model.
    """
    list_display = ('state_name', 'state_execution_order', 'is_dead_end_state', 'required',)
    list_filter = ('is_dead_end_state', 'required',)
    search_fields = ('state_name',)

    class Meta(object):
        model = RetirementState


@admin.register(UserRetirementStatus)
class UserRetirementStatusAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserRetirementStatus model.
    """
    list_display = ('user', 'original_username', 'current_state', 'modified')
    list_filter = ('current_state',)
    raw_id_fields = ('user',)
    search_fields = ('original_username', 'retired_username', 'original_email', 'retired_email', 'original_name')

    class Meta(object):
        model = UserRetirementStatus


@admin.register(UserRetirementRequest)
class UserRetirementRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserRetirementRequest model.
    """
    list_display = ('user', 'created')
    raw_id_fields = ('user',)

    class Meta(object):
        model = UserRetirementRequest


@admin.register(UserRetirementPartnerReportingStatus)
class UserRetirementPartnerReportingStatusAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserRetirementPartnerReportingStatus model.
    """
    list_display = (
        'user_id',  # See user_id() below.
        'original_username',
        'is_being_processed',
        'modified',
    )
    list_filter = ('is_being_processed',)
    raw_id_fields = ('user',)
    search_fields = ('user__id', 'original_username', 'original_email', 'original_name')
    actions = [
        'reset_state',  # See reset_state() below.
    ]

    class Meta(object):
        model = UserRetirementPartnerReportingStatus

    def user_id(self, obj):
        """
        List display for the user_id field.

        This is an alternative to listing the "user" field directly, since that would print the retired (hashed)
        username which isn't super helpful.
        """
        return obj.user.id

    def reset_state(self, request, queryset):
        """
        Action callback for bulk resetting is_being_processed to False (0).
        """
        rows_updated = queryset.update(is_being_processed=0)
        if rows_updated == 1:
            message_bit = "one user was"
        else:
            message_bit = "%s users were" % rows_updated
        self.message_user(request, "%s successfully reset." % message_bit)

    reset_state.short_description = 'Reset is_being_processed to False'
