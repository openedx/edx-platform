from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.api', 'lms.djangoapps.ccx.api')

from lms.djangoapps.ccx.api import *
