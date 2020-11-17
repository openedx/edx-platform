from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_xblock.field_data', 'lms.djangoapps.lms_xblock.field_data')

from lms.djangoapps.lms_xblock.field_data import *
