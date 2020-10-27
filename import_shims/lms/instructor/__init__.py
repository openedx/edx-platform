from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor', 'lms.djangoapps.instructor')

from lms.djangoapps.instructor import *
