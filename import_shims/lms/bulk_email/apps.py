from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.apps', 'lms.djangoapps.bulk_email.apps')

from lms.djangoapps.bulk_email.apps import *
