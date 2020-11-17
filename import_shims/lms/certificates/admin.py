from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.admin', 'lms.djangoapps.certificates.admin')

from lms.djangoapps.certificates.admin import *
