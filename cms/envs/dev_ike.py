# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

# dev environment for ichuang/mit

# FORCE_SCRIPT_NAME = '/cms'

from .common import *
from .dev import *

FEATURES['AUTH_USE_MIT_CERTIFICATES'] = True

FEATURES['USE_DJANGO_PIPELINE'] = False      # don't recompile scss

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')  	# django 1.4 for nginx ssl proxy
