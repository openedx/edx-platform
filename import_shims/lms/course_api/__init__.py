from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api', 'lms.djangoapps.course_api')

from lms.djangoapps.course_api import *
