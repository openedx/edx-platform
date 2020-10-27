from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.models', 'lms.djangoapps.bulk_email.models')

from lms.djangoapps.bulk_email.models import *
