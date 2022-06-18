# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import BlacklistedToken


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'blacklisted_at', )
    list_filter = ('user', )
