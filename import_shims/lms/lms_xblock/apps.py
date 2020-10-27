from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock.apps', 'lms.djangoapps.lms_xblock.apps')

from lms.djangoapps.lms_xblock.apps import *
