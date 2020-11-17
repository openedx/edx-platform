from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_home_api.tests', 'lms.djangoapps.course_home_api.tests')

from lms.djangoapps.course_home_api.tests import *
