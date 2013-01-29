"""
This config file extends the test environment configuration 
so that we can run the lettuce acceptance tests.
"""
from .test import *

# You need to start the server in debug mode,
# otherwise the browser will not render the pages correctly
DEBUG = True

# Show the courses that are in the data directory
COURSES_ROOT = ENV_ROOT / "data"
DATA_DIR = COURSES_ROOT
# MODULESTORE = {
#     'default': {
#         'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
#         'OPTIONS': {
#             'data_dir': DATA_DIR,
#             'default_class': 'xmodule.hidden_module.HiddenDescriptor',
#         }
#     }
# }

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

# Include the lettuce app for acceptance testing, including the 'harvest' django-admin command
INSTALLED_APPS += ('lettuce.django',)
LETTUCE_APPS = ('contentstore',)
LETTUCE_SERVER_PORT = 8001
