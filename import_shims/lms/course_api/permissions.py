from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.permissions', 'lms.djangoapps.course_api.permissions')

from lms.djangoapps.course_api.permissions import *
