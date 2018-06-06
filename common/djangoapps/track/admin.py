'''
django admin pages for courseware model
'''

from django.contrib import admin

from common.djangoapps.track.models import TrackingLog

admin.site.register(TrackingLog)
