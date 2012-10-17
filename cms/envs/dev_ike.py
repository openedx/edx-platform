# dev environment for ichuang/mit

# FORCE_SCRIPT_NAME = '/cms'

from .common import *
from logsettings import get_logger_config
from .dev import *
import socket

MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'] = True

MITX_FEATURES['USE_DJANGO_PIPELINE']=False      # don't recompile scss

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')	# django 1.4 for nginx ssl proxy


