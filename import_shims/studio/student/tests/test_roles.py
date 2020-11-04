from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_roles', 'common.djangoapps.student.tests.test_roles')

from common.djangoapps.student.tests.test_roles import *
