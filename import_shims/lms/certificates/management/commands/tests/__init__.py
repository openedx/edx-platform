from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.management.commands.tests', 'lms.djangoapps.certificates.management.commands.tests')

from lms.djangoapps.certificates.management.commands.tests import *
