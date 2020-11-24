from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.signals', 'lms.djangoapps.grades.signals')

from lms.djangoapps.grades.signals import *
