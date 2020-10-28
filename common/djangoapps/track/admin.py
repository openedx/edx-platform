'''
django admin pages for courseware model
'''

from __future__ import absolute_import

from django.contrib import admin

from track.models import TrackingLog

admin.site.register(TrackingLog)
