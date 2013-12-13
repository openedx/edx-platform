"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /edx-platform  # The location of this repo
        /log  # Where we're going to write log files
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .common import *
from .dev import *
import socket

WIKI_ENABLED = False
FEATURES['ENABLE_TEXTBOOK'] = False
FEATURES['ACCESS_REQUIRE_STAFF_FOR_COURSE'] = True	  # require that user be in the staff_* group to be able to enroll
FEATURES['SUBDOMAIN_COURSE_LISTINGS'] = False
FEATURES['SUBDOMAIN_BRANDING'] = False
FEATURES['FORCE_UNIVERSITY_DOMAIN'] = None		# show all university courses if in dev (ie don't use HTTP_HOST)

FEATURES['DISABLE_START_DATES'] = True
# FEATURES['USE_DJANGO_PIPELINE']=False      # don't recompile scss

myhost = socket.gethostname()
if ('edxvm' in myhost) or ('ocw' in myhost):
    FEATURES['DISABLE_LOGIN_BUTTON'] = True  	# auto-login with MIT certificate
    FEATURES['USE_XQA_SERVER'] = 'https://qisx.mit.edu/xqa'  	# needs to be ssl or browser blocks it
    FEATURES['USE_DJANGO_PIPELINE'] = False      # don't recompile scss

if ('ocw' in myhost):
    FEATURES['ACCESS_REQUIRE_STAFF_FOR_COURSE'] = False

if ('domU' in myhost):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    FEATURES['REROUTE_ACTIVATION_EMAIL'] = 'ichuang@edX.mit.edu'  	# nonempty string = address for all activation emails
    FEATURES['USE_DJANGO_PIPELINE'] = False      # don't recompile scss

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')  	# django 1.4 for nginx ssl proxy

#-----------------------------------------------------------------------------
# disable django debug toolbars

INSTALLED_APPS = tuple([app for app in INSTALLED_APPS if not app.startswith('debug_toolbar')])
MIDDLEWARE_CLASSES = tuple([mcl for mcl in MIDDLEWARE_CLASSES if not mcl.startswith('debug_toolbar')])
#TEMPLATE_LOADERS = tuple([ app for app in TEMPLATE_LOADERS if not app.startswith('edxmako') ])
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
