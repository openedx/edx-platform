'''
django admin pages for courseware model
'''

from external_auth.models import *
from django.contrib import admin

admin.site.register(ExternalAuthMap)
