# -*- coding: utf-8 -*-
"""
Admin configurations for marketplace app
"""
from __future__ import unicode_literals

from django.contrib import admin

from openedx.features.marketplace.models import MarketplaceRequest


class MarketplaceRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'city', 'country')
    search_fields = ('user__username', 'organization__label')
    raw_id_fields = ('user',)


admin.site.register(MarketplaceRequest, MarketplaceRequestAdmin)
