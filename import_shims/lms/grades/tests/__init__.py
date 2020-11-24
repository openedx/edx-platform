from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests', 'lms.djangoapps.grades.tests')

from lms.djangoapps.grades.tests import *
