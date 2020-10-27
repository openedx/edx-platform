from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics.basic', 'lms.djangoapps.instructor_analytics.basic')

from lms.djangoapps.instructor_analytics.basic import *
