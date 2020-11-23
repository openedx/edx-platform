from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.views', 'lms.djangoapps.instructor.tests.views')

from lms.djangoapps.instructor.tests.views import *
