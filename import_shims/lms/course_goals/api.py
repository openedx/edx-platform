from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals.api', 'lms.djangoapps.course_goals.api')

from lms.djangoapps.course_goals.api import *
