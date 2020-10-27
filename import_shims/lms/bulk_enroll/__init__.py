from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_enroll', 'lms.djangoapps.bulk_enroll')

from lms.djangoapps.bulk_enroll import *
