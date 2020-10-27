from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.policies', 'lms.djangoapps.bulk_email.policies')

from lms.djangoapps.bulk_email.policies import *
