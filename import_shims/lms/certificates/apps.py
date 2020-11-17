from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.apps', 'lms.djangoapps.certificates.apps')

from lms.djangoapps.certificates.apps import *
