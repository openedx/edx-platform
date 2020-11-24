from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.views', 'lms.djangoapps.instructor.views')

from lms.djangoapps.instructor.views import *
