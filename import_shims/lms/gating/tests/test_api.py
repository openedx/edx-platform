from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating.tests.test_api', 'lms.djangoapps.gating.tests.test_api')

from lms.djangoapps.gating.tests.test_api import *
