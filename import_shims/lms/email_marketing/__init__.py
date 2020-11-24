from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing', 'lms.djangoapps.email_marketing')

from lms.djangoapps.email_marketing import *
