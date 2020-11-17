from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing.models', 'lms.djangoapps.email_marketing.models')

from lms.djangoapps.email_marketing.models import *
