from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating.tests.test_integration', 'lms.djangoapps.gating.tests.test_integration')

from lms.djangoapps.gating.tests.test_integration import *
