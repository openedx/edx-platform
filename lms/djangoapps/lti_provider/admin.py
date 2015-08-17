"""
Admin interface for LTI Provider app.
"""

from django.contrib import admin

from .models import LtiConsumer

admin.site.register(LtiConsumer)
