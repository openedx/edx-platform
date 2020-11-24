from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.management.commands', 'lms.djangoapps.grades.management.commands')

from lms.djangoapps.grades.management.commands import *
