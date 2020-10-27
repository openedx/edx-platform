from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics.management.commands', 'lms.djangoapps.instructor_analytics.management.commands')

from lms.djangoapps.instructor_analytics.management.commands import *
