from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics.csvs', 'lms.djangoapps.instructor_analytics.csvs')

from lms.djangoapps.instructor_analytics.csvs import *
