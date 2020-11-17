from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.api', 'lms.djangoapps.certificates.api')

from lms.djangoapps.certificates.api import *
