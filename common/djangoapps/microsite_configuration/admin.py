"""
Django admin page for microsite models
"""
from django.contrib import admin

from .models import Microsite


class MicrositeAdmin(admin.ModelAdmin):
    """ Admin interface for the Microsite object. """
    list_display = ('key', 'subdomain')
    search_fields = ('key', 'subdomain', 'values')

    class Meta(object):  # pylint: disable=missing-docstring
        model = Microsite


admin.site.register(Microsite, MicrositeAdmin)
