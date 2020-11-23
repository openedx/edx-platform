from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.base', 'lms.djangoapps.grades.tests.base')

from lms.djangoapps.grades.tests.base import *
