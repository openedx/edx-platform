"""
Django admin page for microsite models
"""
from django.contrib import admin

from .models import Microsite, MicrositeHistory


class MicrositeAdmin(admin.ModelAdmin):
    """ Admin interface for the Microsite object. """
    list_display = ('key', 'subdomain')
    search_fields = ('key', 'subdomain', 'values')

    class Meta(object):  # pylint: disable=missing-docstring
        model = Microsite


class MicrositeHistoryAdmin(admin.ModelAdmin):
    """ Admin interface for the Microsite object. """
    list_display = ('key', 'subdomain', 'created')
    search_fields = ('key', 'subdomain', 'values')

    ordering = ['-created']

    class Meta(object):  # pylint: disable=missing-docstring
        model = MicrositeHistory

    def has_add_permission(self, request):
        """Don't allow adds"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Don't allow deletes"""
        return False


admin.site.register(Microsite, MicrositeAdmin)
admin.site.register(MicrositeHistory, MicrositeHistoryAdmin)
