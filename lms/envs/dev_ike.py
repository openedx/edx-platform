"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /mitx # The location of this repo
        /log  # Where we're going to write log files
"""
from .common import *
from .logsettings import get_logger_config
from .dev import *

WIKI_ENABLED = False
MITX_FEATURES['ENABLE_TEXTBOOK'] = False
MITX_FEATURES['ENABLE_DISCUSSION'] = False
MITX_FEATURES['ACCESS_REQUIRE_STAFF_FOR_COURSE'] = True	  # require that user be in the staff_* group to be able to enroll

#-----------------------------------------------------------------------------
# disable django debug toolbars

INSTALLED_APPS = tuple([ app for app in INSTALLED_APPS if not app.startswith('debug_toolbar') ])
MIDDLEWARE_CLASSES = tuple([ mcl for mcl in MIDDLEWARE_CLASSES if not mcl.startswith('debug_toolbar') ])
