from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.management', 'lms.djangoapps.certificates.management')

from lms.djangoapps.certificates.management import *
