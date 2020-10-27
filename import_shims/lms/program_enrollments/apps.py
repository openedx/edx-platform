from import_shims.warn import warn_deprecated_import

warn_deprecated_import('program_enrollments.apps', 'lms.djangoapps.program_enrollments.apps')

from lms.djangoapps.program_enrollments.apps import *
