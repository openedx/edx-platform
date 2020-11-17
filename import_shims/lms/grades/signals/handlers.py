from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.signals.handlers', 'lms.djangoapps.grades.signals.handlers')

from lms.djangoapps.grades.signals.handlers import *
