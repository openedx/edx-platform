from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.apps', 'lms.djangoapps.grades.apps')

from lms.djangoapps.grades.apps import *
