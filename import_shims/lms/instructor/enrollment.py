from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.enrollment', 'lms.djangoapps.instructor.enrollment')

from lms.djangoapps.instructor.enrollment import *
