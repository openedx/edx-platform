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

