from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics.management', 'lms.djangoapps.instructor_analytics.management')

from lms.djangoapps.instructor_analytics.management import *
