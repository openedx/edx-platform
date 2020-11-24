from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.tests', 'lms.djangoapps.bulk_email.tests')

from lms.djangoapps.bulk_email.tests import *
