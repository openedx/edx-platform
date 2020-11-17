from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests', 'lms.djangoapps.instructor.tests')

from lms.djangoapps.instructor.tests import *
