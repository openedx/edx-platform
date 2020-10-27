from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mailing.management.commands', 'lms.djangoapps.mailing.management.commands')

from lms.djangoapps.mailing.management.commands import *
