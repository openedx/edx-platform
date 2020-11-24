from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_authz', 'common.djangoapps.student.tests.test_authz')

from common.djangoapps.student.tests.test_authz import *
