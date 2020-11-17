from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.management.commands.cert_whitelist', 'lms.djangoapps.certificates.management.commands.cert_whitelist')

from lms.djangoapps.certificates.management.commands.cert_whitelist import *
