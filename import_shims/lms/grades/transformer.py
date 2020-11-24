from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.transformer', 'lms.djangoapps.grades.transformer')

from lms.djangoapps.grades.transformer import *
