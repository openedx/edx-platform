from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.views', 'lms.djangoapps.course_api.views')

from lms.djangoapps.course_api.views import *
