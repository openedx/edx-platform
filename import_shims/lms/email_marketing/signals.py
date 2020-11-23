from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing.signals', 'lms.djangoapps.email_marketing.signals')

from lms.djangoapps.email_marketing.signals import *
