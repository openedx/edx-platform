from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_home_api', 'lms.djangoapps.course_home_api')

from lms.djangoapps.course_home_api import *
