
# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .courses import *

DATABASES = course_db_for('HarvardX/CS50x/2012')
