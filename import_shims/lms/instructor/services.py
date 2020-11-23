from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.services', 'lms.djangoapps.instructor.services')

from lms.djangoapps.instructor.services import *
