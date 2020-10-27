from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing.tests', 'lms.djangoapps.email_marketing.tests')

from lms.djangoapps.email_marketing.tests import *
