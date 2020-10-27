from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock.runtime', 'lms.djangoapps.lms_xblock.runtime')

from lms.djangoapps.lms_xblock.runtime import *
