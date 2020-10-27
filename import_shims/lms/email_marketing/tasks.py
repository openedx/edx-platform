from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing.tasks', 'lms.djangoapps.email_marketing.tasks')

from lms.djangoapps.email_marketing.tasks import *
