from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.permissions', 'lms.djangoapps.instructor.permissions')

from lms.djangoapps.instructor.permissions import *
