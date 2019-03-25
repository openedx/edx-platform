'''
django admin pages for courseware model
'''

from django.contrib import admin

from openedx.core.djangoapps.external_auth.models import ExternalAuthMap


class ExternalAuthMapAdmin(admin.ModelAdmin):
    """
    Admin model for ExternalAuthMap
    """
    search_fields = ['external_id', 'user__username']
    date_hierarchy = 'dtcreated'

admin.site.register(ExternalAuthMap, ExternalAuthMapAdmin)
