from import_shims.warn import warn_deprecated_import

warn_deprecated_import('program_enrollments.api.grades', 'lms.djangoapps.program_enrollments.api.grades')

from lms.djangoapps.program_enrollments.api.grades import *
