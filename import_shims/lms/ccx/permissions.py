from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.permissions', 'lms.djangoapps.ccx.permissions')

from lms.djangoapps.ccx.permissions import *
