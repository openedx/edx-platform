"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /mitx # The location of this repo
        /log  # Where we're going to write log files
"""

import socket

if 'eecs1' in socket.gethostname():
    MITX_ROOT_URL = '/mitx2'

from .common import *
from logsettings import get_logger_config
from .dev import *

if 'eecs1' in socket.gethostname():
    MITX_ROOT_URL = '/mitx2'

#-----------------------------------------------------------------------------
# edx4edx content server

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
MITX_FEATURES['REROUTE_ACTIVATION_EMAIL'] = 'ichuang@mitx.mit.edu'
EDX4EDX_ROOT = ENV_ROOT / "data/edx4edx"

#EMAIL_BACKEND = 'django_ses.SESBackend'

#-----------------------------------------------------------------------------
# ichuang

DEBUG = True
ENABLE_MULTICOURSE = True     # set to False to disable multicourse display (see lib.util.views.mitxhome)
QUICKEDIT = True

MAKO_TEMPLATES['course'] = [DATA_DIR, EDX4EDX_ROOT ]

#MITX_FEATURES['USE_DJANGO_PIPELINE'] = False
MITX_FEATURES['DISPLAY_HISTOGRAMS_TO_STAFF'] = False
MITX_FEATURES['DISPLAY_EDIT_LINK'] = True

COURSE_DEFAULT = "edx4edx"
COURSE_NAME = "edx4edx"
COURSE_NUMBER = "edX.01"
COURSE_TITLE = "edx4edx: edX Author Course"
SITE_NAME = "ichuang.mitx.mit.edu"

COURSE_SETTINGS =  {'edx4edx': {'number' : 'edX.01',
                                    'title'  : 'edx4edx: edX Author Course',
                                    'xmlpath': '/edx4edx/',
                                    'github_url': 'https://github.com/MITx/edx4edx',
                                    'active' : True,
                                    'default_chapter' : 'Introduction',
                                    'default_section' : 'edx4edx_Course',
                                    },
                    }

#-----------------------------------------------------------------------------

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'ssl_auth.ssl_auth.NginxProxyHeaderMiddleware',		# ssl authentication behind nginx proxy
    )

AUTHENTICATION_BACKENDS = (
    'ssl_auth.ssl_auth.SSLLoginBackend',
    'django.contrib.auth.backends.ModelBackend',
    )

INSTALLED_APPS = INSTALLED_APPS + (
    'ssl_auth',
    )

LOGIN_REDIRECT_URL = MITX_ROOT_URL + '/'
LOGIN_URL = MITX_ROOT_URL + '/'
