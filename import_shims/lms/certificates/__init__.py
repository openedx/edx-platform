from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates', 'lms.djangoapps.certificates')

from lms.djangoapps.certificates import *
