from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tasks', 'lms.djangoapps.grades.tasks')

from lms.djangoapps.grades.tasks import *
