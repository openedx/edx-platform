from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.utils', 'lms.djangoapps.instructor.utils')

from lms.djangoapps.instructor.utils import *
