from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.plugins', 'lms.djangoapps.ccx.plugins')

from lms.djangoapps.ccx.plugins import *
