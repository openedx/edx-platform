from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.views', 'lms.djangoapps.bulk_email.views')

from lms.djangoapps.bulk_email.views import *
