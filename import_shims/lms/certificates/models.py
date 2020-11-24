from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.models', 'lms.djangoapps.certificates.models')

from lms.djangoapps.certificates.models import *
