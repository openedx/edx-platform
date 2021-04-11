"""
Django admin page for demographics
"""

from django.contrib import admin

from openedx.core.djangoapps.demographics.models import UserDemographics


class UserDemographicsAdmin(admin.ModelAdmin):
    """
    Admin for UserDemographics Model
    """
    list_display = ('id', 'user', 'show_call_to_action')
    readonly_fields = ('user',)
    search_fields = ('id', 'user__username')

    class Meta(object):
        model = UserDemographics


admin.site.register(UserDemographics, UserDemographicsAdmin)
