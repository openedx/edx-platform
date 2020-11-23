from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.tasks', 'lms.djangoapps.bulk_email.tasks')

from lms.djangoapps.bulk_email.tasks import *
