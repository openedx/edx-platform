# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Idea


class IdeaAdmin(admin.ModelAdmin):
    """Django admin customizations for Idea model."""

    list_display = ('title', 'user', 'user_email', 'organization', 'city', 'country')
    search_fields = ('user__username', 'user__email', 'organization__label')

    def user_email(self, obj):
        """Returning email address of user."""
        return obj.user.email


admin.site.register(Idea, IdeaAdmin)
