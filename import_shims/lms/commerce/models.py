from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.models', 'lms.djangoapps.commerce.models')

from lms.djangoapps.commerce.models import *
