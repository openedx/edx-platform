from import_shims.warn import warn_deprecated_import

warn_deprecated_import('monitoring', 'lms.djangoapps.monitoring')

from lms.djangoapps.monitoring import *
