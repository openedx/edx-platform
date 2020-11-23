from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_enroll.urls', 'lms.djangoapps.bulk_enroll.urls')

from lms.djangoapps.bulk_enroll.urls import *
