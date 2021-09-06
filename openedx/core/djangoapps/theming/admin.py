"""
Django admin page for theming models
"""


from django.contrib import admin

from .models import SiteTheme


class SiteThemeAdmin(admin.ModelAdmin):
    """ Admin interface for the SiteTheme object. """
    list_display = ('site', 'theme_dir_name')
    search_fields = ('site__domain', 'theme_dir_name')

    class Meta(object):
        """
        Meta class for SiteTheme admin model
        """
        model = SiteTheme

admin.site.register(SiteTheme, SiteThemeAdmin)
