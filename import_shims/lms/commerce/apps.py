from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.apps', 'lms.djangoapps.commerce.apps')

from lms.djangoapps.commerce.apps import *
