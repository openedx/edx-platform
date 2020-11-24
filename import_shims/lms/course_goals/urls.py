from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals.urls', 'lms.djangoapps.course_goals.urls')

from lms.djangoapps.course_goals.urls import *
