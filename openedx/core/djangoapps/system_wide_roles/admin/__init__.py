# -*- coding: utf-8 -*-
"""
Django admin integration for system wide roles application.
"""
from django.contrib import admin
from edx_rbac.admin import UserRoleAssignmentAdmin

from openedx.core.djangoapps.system_wide_roles.admin.forms import SystemWideRoleAssignmentForm
from openedx.core.djangoapps.system_wide_roles.models import SystemWideRoleAssignment


@admin.register(SystemWideRoleAssignment)
class SystemWideRoleAssignmentAdmin(UserRoleAssignmentAdmin):
    """
    Django admin model for SystemWideRoleAssignment.
    """
    search_fields = ('user__email', 'role__name')

    form = SystemWideRoleAssignmentForm

    class Meta(object):
        model = SystemWideRoleAssignment
