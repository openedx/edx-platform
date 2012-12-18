"""
This config file extends the test environment configuration 
so that we can run the lettuce acceptance tests.
"""
from .test import *

# You need to start the server in debug mode,
# otherwise the browser will not render the pages correctly
DEBUG = True

# We need to apply the SOUTH migrations to set up the 
# auth tables correctly. Otherwise you'll get an error like this:
# DatabaseError: no such table: auth_registration
SOUTH_TESTS_MIGRATE = True

# Set this up so that rake lms[acceptance] and running the 
# harvest command both use the same (test) database
# which they can flush without messing up your dev db
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "test_mitx.db",
        'TEST_NAME': ENV_ROOT / "db" / "test_mitx.db",     
    }
}

MITX_FEATURES['DISPLAY_TOY_COURSES'] = True
INSTALLED_APPS += ('lettuce.django',)
LETTUCE_APPS = ('portal',)  # dummy app covers the home page, login, registration, and course enrollment
