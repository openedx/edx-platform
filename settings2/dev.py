"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions.
"""
from common import *

CSRF_COOKIE_DOMAIN = 'localhost'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "mitx.db",
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

DEBUG = True
TEMPLATE_DEBUG = False

# This is disabling ASKBOT, but not properly overwriting INSTALLED_APPS. ???
# It's because our ASKBOT_ENABLED here is actually shadowing the real one.
# 
# ASKBOT_ENABLED = True
# MITX_FEATURES['SAMPLE'] = True  # Switch to this system so we get around the shadowing
#
# INSTALLED_APPS = installed_apps()
