from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.api', 'lms.djangoapps.bulk_email.api')

from lms.djangoapps.bulk_email.api import *
