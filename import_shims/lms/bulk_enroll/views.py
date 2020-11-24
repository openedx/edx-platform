from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_enroll.views', 'lms.djangoapps.bulk_enroll.views')

from lms.djangoapps.bulk_enroll.views import *
