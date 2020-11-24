from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.urls', 'lms.djangoapps.bulk_email.urls')

from lms.djangoapps.bulk_email.urls import *
