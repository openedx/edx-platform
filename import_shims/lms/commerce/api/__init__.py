from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api', 'lms.djangoapps.commerce.api')

from lms.djangoapps.commerce.api import *
