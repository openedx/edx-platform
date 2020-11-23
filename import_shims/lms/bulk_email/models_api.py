from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.models_api', 'lms.djangoapps.bulk_email.models_api')

from lms.djangoapps.bulk_email.models_api import *
