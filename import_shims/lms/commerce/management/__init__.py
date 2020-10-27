from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.management', 'lms.djangoapps.commerce.management')

from lms.djangoapps.commerce.management import *
