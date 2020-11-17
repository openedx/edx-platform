from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_analytics.tests.test_csvs', 'lms.djangoapps.instructor_analytics.tests.test_csvs')

from lms.djangoapps.instructor_analytics.tests.test_csvs import *
