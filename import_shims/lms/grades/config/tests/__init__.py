from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.config.tests', 'lms.djangoapps.grades.config.tests')

from lms.djangoapps.grades.config.tests import *
