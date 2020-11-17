from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.api.urls', 'lms.djangoapps.ccx.api.urls')

from lms.djangoapps.ccx.api.urls import *
