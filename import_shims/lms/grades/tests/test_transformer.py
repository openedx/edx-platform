from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_transformer', 'lms.djangoapps.grades.tests.test_transformer')

from lms.djangoapps.grades.tests.test_transformer import *
