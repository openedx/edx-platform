from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests', 'common.djangoapps.student.tests')

from common.djangoapps.student.tests import *
