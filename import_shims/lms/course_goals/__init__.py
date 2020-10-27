from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals', 'lms.djangoapps.course_goals')

from lms.djangoapps.course_goals import *
