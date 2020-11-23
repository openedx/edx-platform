from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.urls', 'lms.djangoapps.ccx.urls')

from lms.djangoapps.ccx.urls import *
