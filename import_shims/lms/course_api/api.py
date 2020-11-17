from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.api', 'lms.djangoapps.course_api.api')

from lms.djangoapps.course_api.api import *
