from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.tests', 'lms.djangoapps.mobile_api.tests')

from lms.djangoapps.mobile_api.tests import *
