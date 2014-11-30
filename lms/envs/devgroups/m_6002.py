
# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .courses import *

DATABASES = course_db_for('MITx/6.002x/2012_Fall')
