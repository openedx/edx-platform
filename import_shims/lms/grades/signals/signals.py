from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.signals.signals', 'lms.djangoapps.grades.signals.signals')

from lms.djangoapps.grades.signals.signals import *
