'''
django admin pages for courseware model
'''

from track.models import TrackingLog
from ratelimitbackend import admin

admin.site.register(TrackingLog)
