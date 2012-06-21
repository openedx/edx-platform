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
from .logsettings import get_logger_config
from .dev import *

if 'eecs1' in socket.gethostname():
    MITX_ROOT_URL = '/mitx2'

#-----------------------------------------------------------------------------
# ichuang

DEBUG = True
ENABLE_MULTICOURSE = True     # set to False to disable multicourse display (see lib.util.views.mitxhome)
QUICKEDIT = True

MITX_FEATURES['USE_DJANGO_PIPELINE'] = False
MITX_FEATURES['DISPLAY_HISTOGRAMS_TO_STAFF'] = False

COURSE_SETTINGS =  {'6.002_Spring_2012': {'number' : '6.002x',
                                          'title'  :  'Circuits and Electronics',
                                          'xmlpath': '/6002x/',
                                          'active' : True,
                                          },
                    '8.02_Spring_2013': {'number' : '8.02x',
                                         'title'  : 'Electricity &amp; Magnetism',
                                         'xmlpath': '/802x/',
                                          'active' : True,
                                         },
                    '8.01_Spring_2013': {'number' : '8.01x',
                                         'title'  : 'Mechanics',
                                         'xmlpath': '/801x/',
                                         'active' : False,
                                         },
                    '6.189_Spring_2013': {'number' : '6.189x',
                                         'title'  : 'IAP Python Programming',
                                         'xmlpath': '/6.189x/',
                                          'active' : True,
                                         },
                    '8.01_Summer_2012': {'number' : '8.01x',
                                         'title'  : 'Mechanics',
                                         'xmlpath': '/801x-summer/',
                                         'active': True,
                                         },
                    'edx4edx': {'number' : 'edX.01',
                                    'title'  : 'edx4edx: edX Author Course',
                                    'xmlpath': '/edx4edx/',
                                    'active' : True,
                                    },
                    '7.03x_Fall_2012': {'number' : '7.03x',
                                    'title'  : 'Genetics',
                                    'xmlpath': '/7.03x/',
                                    'active' : True,
                                    },
                    '18.06x_Linear_Algebra': {'number' : '18.06x',
                                    'title'  : 'Linear Algebra',
                                    'xmlpath': '/18.06x/',
                                    'active' : True,
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
