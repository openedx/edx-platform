from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.utils', 'lms.djangoapps.grades.tests.utils')

from lms.djangoapps.grades.tests.utils import *
