from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock.models', 'lms.djangoapps.lms_xblock.models')

from lms.djangoapps.lms_xblock.models import *
