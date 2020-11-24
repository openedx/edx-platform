from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals.tests', 'lms.djangoapps.course_goals.tests')

from lms.djangoapps.course_goals.tests import *
