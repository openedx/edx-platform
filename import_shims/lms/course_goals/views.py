from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals.views', 'lms.djangoapps.course_goals.views')

from lms.djangoapps.course_goals.views import *
