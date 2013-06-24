'''
django admin pages for courseware model
'''

from track.models import TrackingLog
from django.contrib import admin

admin.site.register(TrackingLog)
