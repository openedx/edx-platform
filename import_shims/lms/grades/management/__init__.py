from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.management', 'lms.djangoapps.grades.management')

from lms.djangoapps.grades.management import *
