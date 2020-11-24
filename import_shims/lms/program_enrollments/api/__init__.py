from import_shims.warn import warn_deprecated_import

warn_deprecated_import('program_enrollments.api', 'lms.djangoapps.program_enrollments.api')

from lms.djangoapps.program_enrollments.api import *
