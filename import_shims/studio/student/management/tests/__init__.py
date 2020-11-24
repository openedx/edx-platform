from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.tests', 'common.djangoapps.student.management.tests')

from common.djangoapps.student.management.tests import *
