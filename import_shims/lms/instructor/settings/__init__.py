from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.settings', 'lms.djangoapps.instructor.settings')

from lms.djangoapps.instructor.settings import *
