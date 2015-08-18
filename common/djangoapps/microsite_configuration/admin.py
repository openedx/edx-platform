"""
Django admin page for microsite models
"""
from django.contrib import admin

from .models import Microsite


admin.site.register(Microsite)
