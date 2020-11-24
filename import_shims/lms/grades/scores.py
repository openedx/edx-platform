from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.scores', 'lms.djangoapps.grades.scores')

from lms.djangoapps.grades.scores import *
