'''
django admin pages for courseware model
'''

from ratelimitbackend import admin

from track.models import TrackingLog

admin.site.register(TrackingLog)
