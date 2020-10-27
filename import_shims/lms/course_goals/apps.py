from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals.apps', 'lms.djangoapps.course_goals.apps')

from lms.djangoapps.course_goals.apps import *
