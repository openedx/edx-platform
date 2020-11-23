from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.signals', 'lms.djangoapps.commerce.signals')

from lms.djangoapps.commerce.signals import *
