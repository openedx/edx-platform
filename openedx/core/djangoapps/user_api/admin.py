"""
Django admin configuration pages for the user_api app
"""
from django.contrib import admin

from .models import RetirementState, UserRetirementStatus, UserRetirementRequest


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
    Admin interface for the UserRetirementStatusAdmin model.
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
    Admin interface for the UserRetirementRequestAdmin model.
    """
    list_display = ('user', 'created')
    raw_id_fields = ('user',)

    class Meta(object):
        model = UserRetirementRequest
