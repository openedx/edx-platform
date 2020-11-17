from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing.admin', 'lms.djangoapps.email_marketing.admin')

from lms.djangoapps.email_marketing.admin import *
