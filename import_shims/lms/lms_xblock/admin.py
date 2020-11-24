from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock.admin', 'lms.djangoapps.lms_xblock.admin')

from lms.djangoapps.lms_xblock.admin import *
