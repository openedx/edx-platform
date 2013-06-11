from .aws import *
import os

USER = os.environ.get('DB_MIGRATION_USER', 'root')
PASSWORD = os.environ.get('DB_MIGRATION_PASS', None)

DATABASES['default']['USER'] = USER
DATABASES['default']['PASSWORD'] = PASSWORD
