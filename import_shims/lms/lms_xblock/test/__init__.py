from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock.test', 'lms.djangoapps.lms_xblock.test')

from lms.djangoapps.lms_xblock.test import *
