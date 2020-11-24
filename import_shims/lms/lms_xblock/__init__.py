from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock', 'lms.djangoapps.lms_xblock')

from lms.djangoapps.lms_xblock import *
