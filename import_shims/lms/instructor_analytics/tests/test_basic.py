from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics.tests.test_basic', 'lms.djangoapps.instructor_analytics.tests.test_basic')

from lms.djangoapps.instructor_analytics.tests.test_basic import *
