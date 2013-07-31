'''
django admin pages for courseware model
'''

from external_auth.models import *
from ratelimitbackend import admin


class ExternalAuthMapAdmin(admin.ModelAdmin):
    search_fields = ['external_id', 'user__username']
    date_hierarchy = 'dtcreated'

admin.site.register(ExternalAuthMap, ExternalAuthMapAdmin)
