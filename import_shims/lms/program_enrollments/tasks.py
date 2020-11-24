from import_shims.warn import warn_deprecated_import

warn_deprecated_import('program_enrollments.tasks', 'lms.djangoapps.program_enrollments.tasks')

from lms.djangoapps.program_enrollments.tasks import *
