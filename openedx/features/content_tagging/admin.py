""" Tagging app admin """
from django.contrib import admin

from .models import TaxonomyOrg

admin.site.register(TaxonomyOrg)
