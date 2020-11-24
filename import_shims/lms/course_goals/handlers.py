from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals.handlers', 'lms.djangoapps.course_goals.handlers')

from lms.djangoapps.course_goals.handlers import *
