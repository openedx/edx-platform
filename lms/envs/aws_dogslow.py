# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

# Import everything from .aws so that our settings are based on those.
from .aws import *

CURRENT_MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES
MIDDLEWARE_CLASSES = ('dogslow.WatchdogMiddleware',) + CURRENT_MIDDLEWARE_CLASSES
# Watchdog is enabled by default, to temporarily disable, set to False:
DOGSLOW = True

# By default, Watchdog will create log files with the backtraces.
# You can also set the location where it stores them:
DOGSLOW_LOG_TO_FILE = True
DOGSLOW_OUTPUT = '/tmp'

# Log requests taking longer than 25 seconds:
DOGSLOW_TIMER = 25

# When both specified, emails backtraces:
DOGSLOW_EMAIL_TO = 'admin@edx.org'
DOGSLOW_EMAIL_FROM = 'no-reply@edx.org'

# Tuple of url pattern names that should not be monitored:
# (defaults to none -- everything monitored)
# Note: this option is not compatible with Django < 1.3
#DOGSLOW_IGNORE_URLS = ('some_view', 'other_view')

# Print (potentially huge!) local stack variables (off by default, use
# True for more detailed, but less manageable reports)
DOGSLOW_STACK_VARS = True

