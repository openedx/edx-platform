from .aws import *
import os

USER = os.environ.get('DB_MIGRATION_USER', 'root')
PASSWORD = os.environ.get('DB_MIGRATION_PASS', None)

if not PASSWORD:
   raise ImproperlyConfigured("No database password was provided for running "
                              "migrations.  This is fatal.")

DATABASES['default']['USER'] = USER
DATABASES['default']['PASSWORD'] = PASSWORD
