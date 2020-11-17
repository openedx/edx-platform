from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.tests.test_overrides', 'lms.djangoapps.ccx.tests.test_overrides')

from lms.djangoapps.ccx.tests.test_overrides import *
