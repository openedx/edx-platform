
# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .courses import *

DATABASES = course_db_for('edX/6.002x/2012_Fall')
