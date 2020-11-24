from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.tests', 'lms.djangoapps.commerce.tests')

from lms.djangoapps.commerce.tests import *
