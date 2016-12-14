"""
Admin site bindings for ccxcon
"""

from django.contrib import admin

from .models import CCXCon

admin.site.register(CCXCon)
