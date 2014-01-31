"""
Reverification admin
"""

from ratelimitbackend import admin
from reverification.models import MidcourseReverificationWindow

admin.site.register(MidcourseReverificationWindow)
