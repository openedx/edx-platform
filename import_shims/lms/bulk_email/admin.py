from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.admin', 'lms.djangoapps.bulk_email.admin')

from lms.djangoapps.bulk_email.admin import *
