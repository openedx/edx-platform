from import_shims.warn import warn_deprecated_import

warn_deprecated_import('program_enrollments', 'lms.djangoapps.program_enrollments')

from lms.djangoapps.program_enrollments import *
