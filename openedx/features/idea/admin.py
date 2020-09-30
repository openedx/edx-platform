# -*- coding: utf-8 -*-
"""
Admin configurations for Idea app
"""
from __future__ import unicode_literals

from django.contrib import admin

from .models import Idea


class IdeaAdmin(admin.ModelAdmin):
    """Django admin customizations for Idea model."""

    list_display = ('title', 'user', 'organization', 'city', 'country')
    search_fields = ('user__username', 'organization__label')
    raw_id_fields = ('user', 'favorites')


admin.site.register(Idea, IdeaAdmin)
