from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock.mixin', 'lms.djangoapps.lms_xblock.mixin')

from lms.djangoapps.lms_xblock.mixin import *
