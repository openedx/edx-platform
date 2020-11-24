from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics.tests', 'lms.djangoapps.instructor_analytics.tests')

from lms.djangoapps.instructor_analytics.tests import *
