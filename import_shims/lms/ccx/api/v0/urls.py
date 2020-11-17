from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.api.v0.urls', 'lms.djangoapps.ccx.api.v0.urls')

from lms.djangoapps.ccx.api.v0.urls import *
