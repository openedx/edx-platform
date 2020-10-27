from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx', 'lms.djangoapps.ccx')

from lms.djangoapps.ccx import *
