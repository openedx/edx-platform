from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.queue', 'lms.djangoapps.certificates.queue')

from lms.djangoapps.certificates.queue import *
