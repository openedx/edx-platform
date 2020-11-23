from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.management.commands.ungenerated_certs', 'lms.djangoapps.certificates.management.commands.ungenerated_certs')

from lms.djangoapps.certificates.management.commands.ungenerated_certs import *
