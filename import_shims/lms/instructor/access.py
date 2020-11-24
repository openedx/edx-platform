from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.access', 'lms.djangoapps.instructor.access')

from lms.djangoapps.instructor.access import *
