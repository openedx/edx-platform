from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_receivers', 'common.djangoapps.student.tests.test_receivers')

from common.djangoapps.student.tests.test_receivers import *
