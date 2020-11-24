from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.signals', 'lms.djangoapps.certificates.signals')

from lms.djangoapps.certificates.signals import *
