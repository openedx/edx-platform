from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.tests.test_model', 'lms.djangoapps.mobile_api.tests.test_model')

from lms.djangoapps.mobile_api.tests.test_model import *
