from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics', 'lms.djangoapps.instructor_analytics')

from lms.djangoapps.instructor_analytics import *
