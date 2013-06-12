"""
A Django settings file for use on AWS while running 
database migrations, since we don't want to normally run the 
LMS with enough privileges to modify the database schema.
"""

# Import everything from .aws so that our settings are based on those.
from .aws import *
import os

USER = os.environ.get('DB_MIGRATION_USER', 'root')
PASSWORD = os.environ.get('DB_MIGRATION_PASS', None)

if not PASSWORD:
   raise ImproperlyConfigured("No database password was provided for running "
                              "migrations.  This is fatal.")

DATABASES['default']['USER'] = USER
DATABASES['default']['PASSWORD'] = PASSWORD
