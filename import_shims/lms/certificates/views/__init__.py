from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.views', 'lms.djangoapps.certificates.views')

from lms.djangoapps.certificates.views import *
