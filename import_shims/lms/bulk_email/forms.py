from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.forms', 'lms.djangoapps.bulk_email.forms')

from lms.djangoapps.bulk_email.forms import *
