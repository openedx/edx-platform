from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.management.commands', 'lms.djangoapps.certificates.management.commands')

from lms.djangoapps.certificates.management.commands import *
