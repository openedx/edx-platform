# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.


class UserRoleAssignmentAdmin(admin.ModelAdmin):
    """
    Django admin model for SystemWideUserRole.
    """

    class Meta(object):
        abstract = True

    fields = (
        'user', 'role'
    )

    list_display = ('user', 'role')
    search_fields = ('user__username', 'role')
