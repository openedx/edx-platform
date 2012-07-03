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
    # MITX_ROOT_URL = '/mitx2'
    MITX_ROOT_URL = 'https://eecs1.mit.edu/mitx2'

#-----------------------------------------------------------------------------
# edx4edx content server

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
MITX_FEATURES['REROUTE_ACTIVATION_EMAIL'] = 'ichuang@mit.edu'
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

COURSE_SETTINGS =  {'6.002x_Fall_2012': {'number' : '6.002x',
                                          'title'  :  'Circuits and Electronics',
                                          'xmlpath': '/6002x-fall-2012/',
                                          'active' : True,
                                          'default_chapter' : 'Week_1',
                                          'default_section' : 'Administrivia_and_Circuit_Elements',
                                          },
                    '8.02_Spring_2013': {'number' : '8.02x',
                                         'title'  : 'Electricity &amp; Magnetism',
                                         'xmlpath': '/802x/',
                                         'github_url': 'https://github.com/MITx/8.02x',
                                         'active' : True,
                                         'default_chapter' : 'Introduction',
                                         'default_section' : 'Introduction_%28Lewin_2002%29',
                                         },
                    '6.189_Spring_2013': {'number' : '6.189x',
                                         'title'  : 'IAP Python Programming',
                                         'xmlpath': '/6.189x/',
                                         'github_url': 'https://github.com/MITx/6.189x',
                                         'active' : True,
                                         'default_chapter' : 'Week_1',
                                         'default_section' : 'Variables_and_Binding',
                                         },
                    '8.01_Fall_2012': {'number' : '8.01x',
                                         'title'  : 'Mechanics',
                                         'xmlpath': '/8.01x/',
                                         'github_url': 'https://github.com/MITx/8.01x',
                                         'active': True,
                                         'default_chapter' : 'MIT_8.011_Spring_2012',
                                         'default_section' : 'Introduction_to_the_course',
                                         },
                    'edx4edx': {'number' : 'edX.01',
                                    'title'  : 'edx4edx: edX Author Course',
                                    'xmlpath': '/edx4edx/',
                                    'github_url': 'https://github.com/MITx/edx4edx',
                                    'active' : True,
                                    'default_chapter' : 'Introduction',
                                    'default_section' : 'edx4edx_Course',
                                    },
                    '7.03x_Fall_2012': {'number' : '7.03x',
                                    'title'  : 'Genetics',
                                    'xmlpath': '/7.03x/',
                                    'github_url': 'https://github.com/MITx/7.03x',
                                    'active' : True,
                                    'default_chapter' : 'Week_2',
                                    'default_section' : 'ps1_question_1',
                                    },
                    '3.091x_Fall_2012': {'number' : '3.091x',
                                    'title'  : 'Introduction to Solid State Chemistry',
                                    'xmlpath': '/3.091x/',
                                    'github_url': 'https://github.com/MITx/3.091x',
                                    'active' : True,
                                    'default_chapter' : 'Week_1',
                                    'default_section' : 'Problem_Set_1',
                                    },
                    '18.06x_Linear_Algebra': {'number' : '18.06x',
                                    'title'  : 'Linear Algebra',
                                    'xmlpath': '/18.06x/',
                                    'github_url': 'https://github.com/MITx/18.06x',
                                    'default_chapter' : 'Unit_1',
                                    'default_section' : 'Midterm_1',
                                    'active' : True,
                                    },
                    '6.00x_Fall_2012': {'number' : '6.00x',
                                    'title'  : 'Introduction to Computer Science and Programming',
                                    'xmlpath': '/6.00x/',
                                    'github_url': 'https://github.com/MITx/6.00x',
                                    'active' : True,
                                    'default_chapter' : 'Week_0',
                                    'default_section' : 'Problem_Set_0',
                                    },
                    '7.00x_Fall_2012': {'number' : '7.00x',
                                    'title'  : 'Introduction to Biology',
                                    'xmlpath': '/7.00x/',
                                    'github_url': 'https://github.com/MITx/7.00x',
                                    'active' : True,
                                    'default_chapter' : 'Unit 1',
                                    'default_section' : 'Introduction',
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
