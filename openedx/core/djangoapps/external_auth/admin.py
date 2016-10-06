'''
django admin pages for courseware model
'''

from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from ratelimitbackend import admin


class ExternalAuthMapAdmin(admin.ModelAdmin):
    """
    Admin model for ExternalAuthMap
    """
    search_fields = ['external_id', 'user__username']
    date_hierarchy = 'dtcreated'

admin.site.register(ExternalAuthMap, ExternalAuthMapAdmin)
