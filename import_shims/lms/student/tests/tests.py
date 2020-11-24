from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.tests', 'common.djangoapps.student.tests.tests')

from common.djangoapps.student.tests.tests import *
