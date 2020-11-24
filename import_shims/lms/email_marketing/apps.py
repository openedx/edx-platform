from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing.apps', 'lms.djangoapps.email_marketing.apps')

from lms.djangoapps.email_marketing.apps import *
