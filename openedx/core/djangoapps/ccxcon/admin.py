"""
Admin site bindings for ccxcon
"""

from __future__ import absolute_import

from django.contrib import admin

from .models import CCXCon

admin.site.register(CCXCon)
