from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.signals', 'lms.djangoapps.bulk_email.signals')

from lms.djangoapps.bulk_email.signals import *
